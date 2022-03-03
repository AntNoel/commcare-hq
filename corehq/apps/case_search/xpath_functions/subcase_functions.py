from collections import Counter
from dataclasses import dataclass

from django.utils.translation import ugettext as _

from eulxml.xpath.ast import BinaryExpression, FunctionCall, Step, serialize

from corehq.apps.es import CaseSearchES, filters, queries

from .exceptions import XPathFunctionException


@dataclass
class SubCaseQuery:
    index_identifier: str
    """The name of the index identifier to match on"""

    subcase_filter: object
    """AST class representing the subcase filter expression"""

    op: str
    """One of ['>', '=']"""

    count: int
    """Integer value used in conjunction with op to filter parent cases"""

    invert: bool
    """True if the initial expression is one of ['<', '<=']"""

    def __post_init__(self):
        ops = ('>', '=')
        if self.op not in ops:
            raise ValueError(f"op must be one of {ops}")

    def as_tuple(self):
        return (
            self.index_identifier, serialize(self.subcase_filter), self.op, self.count, self.invert
        )

    def filter_count(self, count):
        if self.op == '>':
            return count > self.count
        return self.count == count


def subcase(domain, node, fuzzy=False):
    subcase_query = _parse_normalize_subcase_query(node)
    ids = _get_parent_case_ids_matching_subcase_query(domain, subcase_query, fuzzy)
    if subcase_query.invert:
        if not ids:
            return filters.match_all()
        return filters.NOT(filters.doc_id(ids))
    return filters.doc_id(ids)  # TODO handle empty ids


def _get_parent_case_ids_matching_subcase_query(domain, subcase_query, fuzzy=False):
    """Get a list of case IDs for cases that have a subcase with the given index identifier
    and matching the subcase predicate filter.

    Only cases with `[>,=] case_count_gt` subcases will be returned.
    """
    # TODO: validate that the subcase filter doesn't contain any ancestor filtering
    from corehq.apps.case_search.filter_dsl import (
        MAX_RELATED_CASES,
        TooManyRelatedCasesError,
        build_filter_from_ast,
    )

    subcase_filter = build_filter_from_ast(domain, subcase_query.subcase_filter, fuzzy=fuzzy)

    index_query = queries.nested(
        'indices',
        queries.filtered(
            queries.match_all(),
            filters.AND(
                filters.term('indices.identifier', subcase_query.index_identifier),
                filters.NOT(filters.term('indices.referenced_id', ''))  # exclude deleted indices
            )
        )
    )
    es_query = (
        CaseSearchES().domain(domain)
        .filter(index_query)
        .filter(subcase_filter)
        .source('indices')
    )

    if es_query.count() > MAX_RELATED_CASES:
        raise TooManyRelatedCasesError(
            _("The related case lookup you are trying to perform would return too many cases"),
            serialize(subcase_query.subcase_filter)
        )

    parent_case_id_counter = Counter()
    for subcase in es_query.run().hits:
        indices = [index for index in subcase['indices'] if index['identifier'] == subcase_query.index_identifier]
        if indices:
            parent_case_id_counter.update([indices[0]['referenced_id']])

    if subcase_query.op == '>' and subcase_query.count <= 0:
        return list(parent_case_id_counter)

    return [
        case_id for case_id, count in parent_case_id_counter.items() if subcase_query.filter_count(count)
    ]


def _parse_normalize_subcase_query(node) -> SubCaseQuery:
    """Parse the subcase query and normalize it to the form 'subcase-count > N' or 'subcase-count = N'

    Supports the following syntax:
    - subcase-exists('X', {subcase filter} )
    - subcase-count('X', {subcase_filter} ) {=, !=, >, <, >=, <=} {integer value}
    """
    index_identifier, subcase_filter, count_op, case_count = _extract_subcase_query_parts(node)
    case_count, count_op, invert_condition = _normalize_param(case_count, count_op)
    return SubCaseQuery(index_identifier, subcase_filter, count_op, case_count, invert_condition)


def _normalize_param(case_count, count_op):
    invert_condition = False
    if count_op == "<":
        # count < N -> not( count > N - 1 )
        count_op = ">"
        invert_condition = not invert_condition
        case_count -= 1
    elif count_op == "<=":
        # count <= N -> not( count > N )
        count_op = ">"
        invert_condition = not invert_condition
    elif count_op == ">=":
        # count >= N -> count > N -1
        count_op = ">"
        case_count -= 1
    elif count_op == "!=":
        # count != N -> not( count = N )
        count_op = '='
        invert_condition = not invert_condition
    if count_op == "=" and case_count == 0:
        # count = 0 -> not( count > 0 )
        count_op = ">"
        invert_condition = not invert_condition
    return case_count, count_op, invert_condition


def _extract_subcase_query_parts(node):
    current_node = node
    if isinstance(node, BinaryExpression):
        count_op = node.op
        case_count = node.right
        current_node = node.left

        if count_op not in [">", "<", "<=", ">=", "=", "!="]:
            raise XPathFunctionException(
                _("Unsupported operator for use with 'subcase-count': {op}").format(op=count_op),
                serialize(node)
            )

        try:
            case_count = int(case_count)
        except ValueError:
            raise XPathFunctionException(
                _("'subcase-count' must be compared to a positive integer"),
                serialize(node)
            )

        if case_count < 0:
            raise XPathFunctionException(
                _("'subcase-count' must be compared to a positive integer"),
                serialize(node)
            )

        if not isinstance(current_node, FunctionCall) or str(current_node.name) != "subcase-count":
            raise XPathFunctionException(
                _("XPath incorrectly formatted. Expected 'subcase-count'"),
                serialize(current_node)
            )

    else:
        if not isinstance(node, FunctionCall) or str(node.name) != "subcase-exists":
            raise XPathFunctionException(
                _("XPath incorrectly formatted. Expected 'subcase-exists'"),
                serialize(node)
            )

        case_count = 0
        count_op = ">"

    index_identifier = current_node.args[0]
    subcase_filter = current_node.args[1]

    return index_identifier, subcase_filter, count_op, case_count
