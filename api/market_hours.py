class MarketHours:
    """Initiates MarketHours object to store the market hours for each timezone in USA.

    >>> MarketHours

    See Also:
        Class variable ``hours`` contains key-value pairs for both ``EXTENDED`` and ``REGULAR`` market hours.
    """

    hours = {
        'EXTENDED': {
            'EDT': {'OPEN': 4, 'CLOSE': 20}, 'EST': {'OPEN': 4, 'CLOSE': 20},
            'CDT': {'OPEN': 3, 'CLOSE': 19}, 'CST': {'OPEN': 3, 'CLOSE': 19},
            'MDT': {'OPEN': 2, 'CLOSE': 18}, 'MST': {'OPEN': 2, 'CLOSE': 18},
            'PDT': {'OPEN': 1, 'CLOSE': 17}, 'PST': {'OPEN': 1, 'CLOSE': 17}
        },
        'REGULAR': {
            'EDT': {'OPEN': 9, 'CLOSE': 16}, 'EST': {'OPEN': 9, 'CLOSE': 16},
            'CDT': {'OPEN': 8, 'CLOSE': 15}, 'CST': {'OPEN': 8, 'CLOSE': 15},
            'MDT': {'OPEN': 7, 'CLOSE': 14}, 'MST': {'OPEN': 7, 'CLOSE': 14},
            'PDT': {'OPEN': 6, 'CLOSE': 13}, 'PST': {'OPEN': 6, 'CLOSE': 13}
        }
    }
