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


class CustomTemplate:
    """Initiates Template object which has the template for static html file stored.

    >>> CustomTemplate

    """

    source = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>Robinhood Portfolio</title>
        <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
        <meta http-equiv="Pragma" content="no-cache">
        <meta http-equiv="Expires" content="0">
        <!-- Disables 404 for favicon.ico which is a logo on top of the webpage tab -->
        <link rel="shortcut icon" href="#">
    </head>
    <style type="text/css">
        @import url('//netdna.bootstrapcdn.com/font-awesome/4.6.3/css/font-awesome.min.css');
        body{
            font-family: 'PT Serif', serif;
            background-color: #ececec;
        }
        .night{
        background-color: #151515;
        }
        .toggler{
            font-size: 28px;
            border-radius: 100px;
            background-color: #111111;
            padding: 15px;
            color:#fcfcfc;
            box-shadow: 1px 2px 6px rgba(0,0,0,.3);
            cursor: pointer;
            position: fixed;
            bottom:20px;
            right: 20px;
            -webkit-transition: all 0.2s;
            -moz-transition: all 0.2s;
            transition: all 0.2s;
        }
        .fa-moon-o:before{
            padding:0 2px;
        }
        .fa-sun-o{
            background-color: #212121;
            color:#ccc;
        }
        /* Optional */
        .content{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            box-shadow: 0 4px 24px 0 #ddd;
            box-sizing: border-box;
            padding: 20px;
            font-family: arial;
        }
        .content h1{
            font-size: 58px;
            font-weight: 100;
            margin: 0 0 20px;
        }
        .content .text{
            line-height: 23px;
            font-size: 15px;
            color: #444;
        }
        .night *{
            color: #f0f0f0 !important;
            box-shadow: none;
        }
        .night .content{
            border: 1px solid #999;
        }
    </style>
    <style>
        .tab {
            margin-left: 40px;
        }
        p.center {
            text-align: center;
        }
        div {
            height: 1em;
        }
        .dotted {
            border-bottom: 3px dotted #757575;
            margin-bottom: 1px;
        }
        .cent {
            margin-top: 1%;
            text-align: center;
            font-size: 120%;
        }
    </style>
    <body translate="no">
        <div class="toggler fa fa-moon-o"></div>
        <p class="center">{{ TITLE }}</p>
        <p class="tab"><span style="white-space: pre-line">{{ SUMMARY }}</span></p>

        <div class="dotted"></div>
        <div class="cent">Profit</div>

        <div class="dotted"></div>
        <p class="tab"><span style="white-space: pre-line">{{ PROFIT }}</span></p>

        <div class="dotted"></div>
        <div class="cent">Loss</div>

        <div class="dotted"></div>
        <p class="tab"><span style="white-space: pre-line">{{ LOSS }}</span></p>

        <div class="dotted"></div>
        <div class="cent">Watchlist</div>

        <div class="dotted"></div>
        <p class="tab"><span style="white-space: pre-line">{{ WATCHLIST_UP }}</span></p>
        <p class="tab"><span style="white-space: pre-line">{{ WATCHLIST_DOWN }}</span></p>
        <br><br>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.2.2/jquery.min.js"></script>
    <script id="rendered-js">
        var theme = window.localStorage.currentTheme;
        $('body').addClass(theme);
        if ($("body").hasClass("night")) {
            $('.toggler').addClass('fa-sun-o');
            $('.toggler').removeClass('fa-moon-o');
        } else {
            $('.toggler').removeClass('fa-sun-o');
            $('.toggler').addClass('fa-moon-o');
        }
        $('.toggler').click(function () {
        $('.toggler').toggleClass('fa-sun-o');
        $('.toggler').toggleClass('fa-moon-o');
        if ($("body").hasClass("night")) {
            $('body').toggleClass('night');
            localStorage.removeItem('currentTheme');
            localStorage.currentTheme = "day";
        } else {
            $('body').toggleClass('night');
            localStorage.removeItem('currentTheme');
            localStorage.currentTheme = "night";
        }
        });
        //# sourceURL=pen.js
    </script>
    </body>
</html>
"""
