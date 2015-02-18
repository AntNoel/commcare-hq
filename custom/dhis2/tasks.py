"""
Celery tasks used by the World Vision Sri Lanka Nutrition project

Two tasks are executed daily:

  * sync_org_units: Synchronize DHIS2 Organization Units with local data

  * sync_child_entities: Create new child cases in CommCare for nutrition
    tracking, and associate CommCare child cases with DHIS2 child entities
    and enroll them in the Pediatric Nutrition Assessment and Underlying Risk
    Assessment programs.

Creating program events for Nutrition Assessment and Risk Assessment programs
is done using FormRepeater payload generators. See payload_generators.py for
details.

"""
from datetime import date, timedelta
import logging
import uuid
from xml.etree import ElementTree
from casexml.apps.case.mock import CaseBlock
from casexml.apps.case.models import CommCareCase
from casexml.apps.case.xml import V2
# from celery.schedules import crontab
from celery.task import periodic_task
from corehq.apps.es import CaseES, UserES
from corehq.apps.hqcase.utils import submit_case_blocks, get_case_by_identifier
from corehq.apps.users.models import CommCareUser
from custom.dhis2.const import CCHQ_CASE_ID, NUTRITION_ASSESSMENT_PROGRAM_FIELDS, ORG_UNIT_FIXTURES, CASE_TYPE, \
    TRACKED_ENTITY
from custom.dhis2.models import Dhis2Api, Dhis2OrgUnit, Dhis2Settings, FixtureManager


logger = logging.getLogger(__name__)


def push_child_entities(settings, children):
    """
    Register child entities in DHIS2 and enroll them in the Pediatric
    Nutrition Assessment program.

    :param children: child_gmp cases where external_id is not set

    .. Note:: Once pushed, external_id is set to the ID of the
              tracked entity instance.

    This fulfills the second requirement of `DHIS2 Integration`_.


    .. _DHIS2 Integration: https://www.dropbox.com/s/8djk1vh797t6cmt/WV Sri Lanka Detailed Requirements.docx
    """
    dhis2_api = Dhis2Api(settings.dhis2['host'], settings.dhis2['username'], settings.dhis2['password'],
                         settings.dhis2['top_org_unit_name'])
    # nutrition_id = dhis2_api.get_program_stage_id('Nutrition Assessment')
    nutrition_id = dhis2_api.get_program_id('Paediatric Nutrition Assessment')
    today = date.today()
    for child in children:
        if getattr(child, 'dhis_org_id', None):
            ou_id = child.dhis_org_id  # App sets this case property from user custom data
        else:
            # This is an old case, or org unit is not set. Skip it
            continue
        try:
            # Search for CCHQ Case ID in case previous attempt to register failed.
            dhis2_child = next(dhis2_api.gen_instances_with_equals(TRACKED_ENTITY, CCHQ_CASE_ID, child['_id']))
            dhis2_child_id = dhis2_child['Instance']
        except StopIteration:
            # Register child entity in DHIS2, and set CCHQ Case ID.
            dhis2_child = {
                CCHQ_CASE_ID: child['_id'],
            }
            dhis2_child_id = dhis2_api.add_te_inst(TRACKED_ENTITY, ou_id, dhis2_child)

        # Enroll in Pediatric Nutrition Assessment
        date_of_visit = child['date_of_visit'] if getattr(child, 'date_of_visit', None) else today
        program_data = {dhis2_attr: child[cchq_attr]
                        for cchq_attr, dhis2_attr in NUTRITION_ASSESSMENT_PROGRAM_FIELDS.iteritems()
                        if getattr(child, cchq_attr, None)}
        if (
            'CHDR Number' in NUTRITION_ASSESSMENT_PROGRAM_FIELDS.values() and  # May not be required in production
            'CHDR Number' not in program_data
        ):
            # CHDR Number must have a unique value. If we don't have one, we have to fake it.
            program_data['CHDR Number'] = 'cchq-' + child['_id']
        response = dhis2_api.enroll_in_id(dhis2_child_id, nutrition_id, date_of_visit, program_data)
        if response['status'] != 'SUCCESS':
            logger.error('Failed to push CCHQ case "%s" to DHIS2 program "%s". DHIS2 API error: %s',
                         child['_id'], 'Paediatric Nutrition Assessment', response)
            # Skip to the next case
            continue

        # Set external_id in CCHQ to flag the case as pushed.
        update_case_external_id(child, dhis2_child_id)


def pull_child_entities(settings, dhis2_children):
    """
    Create new child cases for nutrition tracking in CommCare.

    Sets external_id on new child cases, and CCHQ Case ID on DHIS2
    tracked entity instances. (CCHQ Case ID is initially unset because the
    case is new and does not exist in CommCare.)

    :param settings: DHIS2 settings, incl. relevant domain
    :param dhis2_children: A list of dictionaries of TRACKED_ENTITY (i.e.
                           "Child") tracked entities from the DHIS2 API where
                           CCHQ Case ID is unset

    This fulfills the third requirement of `DHIS2 Integration`_.


    .. _DHIS2 Integration: https://www.dropbox.com/s/8djk1vh797t6cmt/WV Sri Lanka Detailed Requirements.docx
    """
    dhis2_api = Dhis2Api(settings.dhis2['host'], settings.dhis2['username'], settings.dhis2['password'],
                         settings.dhis2['top_org_unit_name'])
    for dhis2_child in dhis2_children:
        # Add each child separately. Although this is slower, it avoids problems if a DHIS2 API call fails
        # ("Instance" is DHIS2's friendly name for "id")
        logger.info('DHIS2: Syncing DHIS2 child "%s"', dhis2_child['Instance'])
        case = get_case_by_external_id(settings.domain, dhis2_child['Instance'])
        if case:
            case_id = case['case_id']
        else:
            user = get_user_by_org_unit(settings.domain, dhis2_child['Org unit'],
                                        settings.dhis2['top_org_unit_name'])
            if not user:
                # No user is assigned to this or any higher organisation unit
                logger.error('DHIS2: Unable to import DHIS2 instance "%s"; there is no user at org unit "%s" or '
                             'above to assign the case to.', dhis2_child['Instance'], dhis2_child['Org unit'])
                continue
            case_id = create_case_from_dhis2(dhis2_child, settings.domain, user)
        dhis2_child[CCHQ_CASE_ID] = case_id
        dhis2_api.update_te_inst(dhis2_child)


def get_user_by_org_unit(domain, org_unit_id, top_org_unit_name):
    """
    Look up user ID by a DHIS2 organisation unit ID
    """
    result = (UserES()
              .domain(domain)
              .term('user_data.dhis_org_id', org_unit_id)
              .run())
    if result.total:
        # Don't just assign all cases to the first user. Spread them fairly.
        i = random.randrange(result.total)
        return CommCareUser.wrap(result.hits[i])
    # No user is assigned to this organisation unit (i.e. region or facility).
    # Try its parent org unit.
    Dhis2OrgUnit.objects = FixtureManager(Dhis2OrgUnit, domain, ORG_UNIT_FIXTURES)
    org_units = {ou.id: ou for ou in Dhis2OrgUnit.objects.all()}
    if (
        org_unit_id in org_units and
        org_units[org_unit_id].name != top_org_unit_name and
        org_units[org_unit_id].parent_id
    ):
        return get_user_by_org_unit(domain, org_units[org_unit_id].parent_id, top_org_unit_name)
    # We don't know that org unit ID, or we're at the top for this project, or we're at the top of DHIS2
    return None


def get_case_by_external_id(domain, external_id):
    """
    Filter cases by external_id
    """
    return get_case_by_identifier(domain, external_id)


def create_case_from_dhis2(dhis2_child, domain, user):
    """
    Create a new case using the data pulled from DHIS2

    :param dhis2_child: TRACKED_ENTITY (i.e. "Child") from DHIS2
    :param domain: (str) The name of the domain
    :param user: (Document) The owner of the new case
    :return: New case ID
    """
    case_id = uuid.uuid4().hex
    update = {k: dhis2_child[v] for k, v in NUTRITION_ASSESSMENT_PROGRAM_FIELDS.iteritems()}
    caseblock = CaseBlock(
        create=True,
        case_id=case_id,
        owner_id=user.userID,
        user_id=user.userID,
        version=V2,
        case_type=CASE_TYPE,
        external_id=dhis2_child['Instance'],
        update=update
    )
    casexml = ElementTree.tostring(caseblock.as_xml())
    submit_case_blocks(casexml, domain)
    return case_id


def update_case_external_id(case, external_id):
    """
    Update the external_id of a case
    """
    caseblock = CaseBlock(
        create=False,
        case_id=case['_id'],
        version=V2,
        external_id=external_id
    )
    casexml = ElementTree.tostring(caseblock.as_xml())
    submit_case_blocks(casexml, case['domain'])


def get_children_only_theirs(settings):
    """
    Returns a list of child entities that are enrolled in Paediatric Nutrition
    Assessment and don't have CCHQ Case ID set.
    """
    dhis2_api = Dhis2Api(settings.dhis2['host'], settings.dhis2['username'], settings.dhis2['password'],
                         settings.dhis2['top_org_unit_name'])
    for inst in dhis2_api.gen_instances_in_program('Paediatric Nutrition Assessment'):
        if not inst.get(CCHQ_CASE_ID):
            yield inst


def gen_children_only_ours(domain):
    """
    Returns a list of child_gmp cases where external_id is not set
    """
    result = (CaseES()
              .domain(domain)
              .case_type(CASE_TYPE)
              .empty('external_id')
              .run())
    if result.total:
        for doc in result.hits:
            yield CommCareCase.wrap(doc)


# TODO: Use case forwarding, or form forwarding of registration forms
@periodic_task(run_every=timedelta(minutes=5))  # Run every 5 minutes to match forwarded forms
def sync_cases():
    """
    Create new child cases in CommCare for nutrition tracking, and associate
    CommCare child cases with DHIS2 child entities and enroll them in the
    Pediatric Nutrition Assessment and Underlying Risk Assessment programs.
    """
    for settings in Dhis2Settings.all_enabled():
        logger.info('DHIS2: Syncing cases for domain "%s" with "%s"',
                    settings.domain, settings.dhis2['host'])
        children = get_children_only_theirs(settings)
        pull_child_entities(settings, children)

        children = gen_children_only_ours(settings.domain)
        push_child_entities(settings, children)


# @periodic_task(run_every=crontab(minute=3, hour=3))  # Run daily at 03h03
# dhis.pgim.cmb.ac.lk has over 10 000 org units. Not practical to store on handsets.
def sync_org_units():
    """
    Synchronize DHIS2 Organization Units with local data.

    This data is used to fulfill the first requirement of
    `DHIS2 Integration`_: Allow mobile users in CommCareHQ to be
    associated with a particular DHIS2 Organisation Unit, so that when
    they create cases their new cases can be associated with that area
    or facility.


    .. _DHIS2 Integration: https://www.dropbox.com/s/8djk1vh797t6cmt/WV Sri Lanka Detailed Requirements.docx

    """
    for settings in Dhis2Settings.all_enabled():
        logger.info('DHIS2: Syncing org units for domain "%s" with "%s"',
                    settings.domain, settings.dhis2['host'])
        dhis2_api = Dhis2Api(settings.dhis2['host'], settings.dhis2['username'], settings.dhis2['password'],
                             settings.dhis2['top_org_unit_name'])
        Dhis2OrgUnit.objects = FixtureManager(Dhis2OrgUnit, settings.domain, ORG_UNIT_FIXTURES)
        our_org_units = {ou.id: ou for ou in Dhis2OrgUnit.objects.all()}
        their_org_units = {}
        # Add new org units
        for ou in dhis2_api.gen_org_units():
            their_org_units[ou['id']] = ou
            if ou['id'] not in our_org_units:
                logger.info('DHIS2: Adding org unit "%s"', ou['name'])
                org_unit = Dhis2OrgUnit(id=ou['id'], name=ou['name'],
                                        parent_id=dhis2_api.get_org_unit_parent_id(ou['id']))
                org_unit.save()
        # Delete former org units
        for id_, ou in our_org_units.iteritems():
            if id_ not in their_org_units:
                logger.info('DHIS2: Deleting org unit "%s"', ou.name)
                ou.delete()
