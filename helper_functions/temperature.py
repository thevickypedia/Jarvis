def c2f(arg):
    """Converts Celcius to Farenheit"""
    return round(((arg / 5) * 9) + 32, 2)


def f2c(arg):
    """Converts Farenheit to Celcius"""
    return round(((arg - 32) / 9) * 5, 2)


def c2k(arg):
    """Converts Celcius to Kelvin"""
    return arg + 273.15


def k2c(arg):
    """Converts Kelvin to Celcius"""
    return arg - 273.15


def k2f(arg):
    """Converts Kelvin to Celcius"""
    return round((arg * 1.8) - 459.69, 2)


def f2k(arg):
    """Converts Farenheit to Kelvin"""
    return round((arg + 459.67) / 1.8, 2)
