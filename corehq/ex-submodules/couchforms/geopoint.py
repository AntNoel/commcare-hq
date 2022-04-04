import re
from collections import namedtuple
from decimal import Decimal, InvalidOperation

from jsonobject.exceptions import BadValueError


class GeoPoint(namedtuple('GeoPoint', 'latitude longitude altitude accuracy')):
    @property
    def lat_lon(self):
        return {
            'lat': self.latitude,
            'lon': self.longitude
        }

    @classmethod
    def from_string(cls, input_string):
        try:
            latitude, longitude, altitude, accuracy = input_string.split(' ')
        except (TypeError, AttributeError, ValueError):
            raise BadValueError("GeoPoint format expects 4 decimals: {!r}"
                                .format(input_string))
        try:
            # this should eventually be removed once it's fixed on the mobile
            # the mobile sometimes submits in scientific notation
            # but only comes up for very small values
            # http://manage.dimagi.com/default.asp?159863
            latitude = _canonical_decimal_round_tiny_exp(latitude)
            longitude = _canonical_decimal_round_tiny_exp(longitude)
            altitude = _canonical_decimal_round_tiny_exp(altitude)
            accuracy = _canonical_decimal_round_tiny_exp(accuracy)
        except ValueError:
            raise BadValueError("{!r} is not a valid format GeoPoint format"
                                .format(input_string))
        return GeoPoint(latitude, longitude, altitude, accuracy)


def _canonical_decimal(n):
    """
    raises ValueError for non-canonically formatted decimal strings

    example: '00.1' or '.1' whose canonical form is '0.1'

    """
    value_error = False
    try:
        decimal = Decimal(n)
    except InvalidOperation:
        value_error = True
    if value_error:
        raise ValueError('{!r} is not a canonically formatted decimal'
                         .format(n))
    return decimal


def _canonical_decimal_round_tiny_exp(n):
    """
    Same behavior as _canonical_decimal, but also accepts small values in
    scientific notation, rounding them to zero

    """
    exp_match = re.match(r'^-?\d.\d+E-(\d)$', n)
    if exp_match:
        e = int(exp_match.group(1))
        if e < 4:
            raise ValueError('Hack for scientific notation only works for '
                             'negative exponents 4 and above: {!r}'.format(n))
        else:
            return Decimal('0')
    else:
        return _canonical_decimal(n)
