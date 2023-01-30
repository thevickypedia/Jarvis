# noinspection PyUnresolvedReferences
"""Convert common temperature values used in the main module.

>>> Temperature

"""


def c2f(arg: float) -> float:
    """Converts ``Celcius`` to ``Farenheit``.

    Args:
        arg: Takes ``Celcius`` value as argument.

    Returns:
        float:
        Converted ``Farenheit`` value.

    """
    return round(((arg / 5) * 9) + 32, 2)


def f2c(arg: float) -> float:
    """Converts ``Farenheit`` to ``Celcius``.

    Args:
        arg: Takes ``Farenheit`` value as argument.

    Returns:
        float:
        Converted ``Celcius`` value.

    """
    return round(((arg - 32) / 9) * 5, 2)


def c2k(arg: float) -> float:
    """Converts ``Celcius`` to ``Kelvin``.

    Args:
        arg: Takes ``Celcius`` value as argument.

    Returns:
        float:
        Converted ``Kelvin`` value.

    """
    return arg + 273.15


def k2c(arg: float) -> float:
    """Converts ``Kelvin`` to ``Celcius``.

    Args:
        arg: Takes ``Kelvin`` value as argument.

    Returns:
        float:
        Converted ``Celcius`` value.

    """
    return arg - 273.15


def k2f(arg: float) -> float:
    """Converts ``Kelvin`` to ``Celcius``.

    Args:
        arg: Takes ``Kelvin`` value as argument.

    Returns:
        float:
        Converted ``Farenheit`` value.

    """
    return round((arg * 1.8) - 459.69, 2)


def f2k(arg: float) -> float:
    """Converts ``Farenheit`` to ``Kelvin``.

    Args:
        arg: Taken ``Farenheit`` value as argument.

    Returns:
        float:
        Converted ``Kelvin`` value.

    """
    return round((arg + 459.67) / 1.8, 2)
