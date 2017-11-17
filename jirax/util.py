"""Utilities."""

from collections.abc import Iterable


def is_of_type(value, expected_types):
    """Check if the given value is of an expected type.

    The expected types are given as a single type or type name, or an iterable
    of them.

    :param value: the value to check.
    :param expected_types: the expected type(s).
    :return: `True` iff the given value is of an expected type.
    :rtype: `bool`
    """
    if isinstance(expected_types, type) or isinstance(expected_types, str):
        expected_types = [expected_types]
    expected_real_types = set()
    expected_type_names = set()
    for expected_type in expected_types:
        assert isinstance(expected_type, (type, str))
        if isinstance(expected_type, type):
            expected_real_types.add(expected_type)
        else:
            expected_type_names.add(expected_type)
    value_type = type(value)
    return (isinstance(value, tuple(expected_real_types)) or
            value_type.__name__ in expected_type_names or
            value_type.__qualname__ in expected_type_names)


def type_names(types):
    """Yield type names."""
    if isinstance(types, type) or isinstance(types, str):
        types = [types]
    return (type_.__qualname__ if isinstance(type_, type) else type_
            for type_ in types)


def check_type(value, expected_types):
    """Ensure that the given value is of an expected type.

    The expected types are given as a single type or type name, or an iterable
    of them.

    :param value: the value to check.
    :param expected_types: the expected type(s).
    :raise `TypeError`: if *value* is not of the *expected_types*.
    """
    if is_of_type(value, expected_types):
        return
    if isinstance(expected_types, type) or isinstance(expected_types, str):
        expected_types = [expected_types]
    raise TypeError("type of {!r} is {} but should be one of: {}"
                    .format(value, type(value).__qualname__,
                            ", ".join(type_names(expected_types))))
