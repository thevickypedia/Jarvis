def c2f(arg: float):
    """Converts Celcius to Farenheit.

    Args:
        arg: Takes Celcius value as argument.

    Returns: Converted Farenheit value.

    """
    return round(((arg / 5) * 9) + 32, 2)


def f2c(arg: float):
    """Converts Farenheit to Celcius.

    Args:
        arg: Takes Farenheit value as argument.

    Returns: Converted Celcius value.

    """
    return round(((arg - 32) / 9) * 5, 2)


def c2k(arg: float):
    """Converts Celcius to Kelvin.

    Args:
        arg: Takes Celcius value as argument.

    Returns: Converted Kelvin value.

    """
    return arg + 273.15


def k2c(arg: float):
    """Converts Kelvin to Celcius.

    Args:
        arg: Takes Kelvin value as argument.

    Returns: Converted Celcius value.

    """
    return arg - 273.15


def k2f(arg: float):
    """Converts Kelvin to Celcius.

    Args:
        arg: Takes Kelvin value as argument.

    Returns: Converted Farenheit value.

    """
    return round((arg * 1.8) - 459.69, 2)


def f2k(arg: float):
    """Converts Farenheit to Kelvin.

    Args:
        arg: Taken Farenheit value as argument.

    Returns: Converted Kelvin value.

    """
    return round((arg + 459.67) / 1.8, 2)
