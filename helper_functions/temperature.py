def c2f(arg):
    return round(((arg / 5) * 9) + 32, 2)


def f2c(arg):
    return round(((arg - 32) / 9) * 5, 2)


def c2k(arg):
    return arg + 273.15


def k2c(arg):
    return arg - 273.15


def k2f(arg):
    return round((arg * 1.8) - 459.69, 2)


def f2k(arg):
    return round((arg + 459.67) / 1.8, 2)


def r2c(arg):
    return arg * 1.25


def c2r(arg):
    return round(arg * 0.8, 2)


def r2k(arg):
    return c2k(r2c(arg))
