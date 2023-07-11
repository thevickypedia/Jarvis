# noinspection PyUnresolvedReferences
"""List of keywords for each variable which is condition matched in the main module.

>>> KeywordsBase

"""

from collections import OrderedDict
from typing import List

keywords: OrderedDict = OrderedDict()


def keyword_mapping() -> OrderedDict[str, List[str]]:
    """Returns an ordered dictionary of base keywords mapping.

    See Also:
        - Keywords should have both singular and plural forms wherever possible.
        - An alternate is to use

        .. code-block:: python

            import inflect
            engine = inflect.engine()
            engine.plural(phrase)
            engine.singular_noun(phrase)

        - But the approach is time taking and inconsistent.

    Returns:
        OrderedDict:
        OrderedDict of category and keywords as key-value pairs.
    """
    return OrderedDict(
        listener_control=['listener'],
        send_notification=['message', 'text', 'sms', 'mail', 'email', 'messages', 'mails', 'emails'],
        lights=['light', 'party mode', 'lights'],
        television=['tv', 'television', 'tvs', 'televisions', "tv's", "television's"],
        volume=['volume', 'mute'],
        car=['car', 'vehicle'],
        garage=['garage'],
        weather=['weather', 'temperature', 'sunrise', 'sun rise', 'sunset', 'sun set'],

        # ORDER OF THE ABOVE SHOULD BE RETAINED, AS THE CONDITION LOOP WILL RUN IN THE SAME ORDER
        # internal

        meetings=['meeting', 'meetings'],
        events=['event', 'events'],
        current_date=["today's date", 'current date', 'what is the date', "what's the date", 'todays date',
                      'whats the date'],
        current_time=['current time', 'time now', 'time in', 'what is the time', "what's the time", 'whats the time'],
        system_info=['configuration', 'system config'],
        ip_info=['address'],
        wikipedia_=['wikipedia', 'info', 'information'],
        news=['news'],
        report=['report'],
        robinhood=['robinhood', 'investment', 'portfolio', 'summary'],
        repeat=['repeat'],
        location=['location', 'where are you'],
        locate=['locate', 'where is my', "where's my", 'wheres my'],
        read_gmail=['email', 'mail', 'mails', 'emails'],
        meaning=['meaning', 'dictionary', 'definition', 'meanings', 'definitions'],
        todo=['plan', 'to do', 'to-do', 'todo', 'plans'],
        kill_alarm=['stop alarm', 'stop my alarm', 'stop another alarm', 'stop an alarm', 'stop timer', 'stop my timer',
                    'stop another timer', 'stop an timer', 'turn off my alarm', 'turn my alarm off',
                    'stop another alarm', 'turn off alarm', 'turn off my timer', 'turn my timer off',
                    'stop another timer', 'turn off timer', 'delete alarm', 'delete my alarm', 'delete another alarm',
                    'delete an alarm', 'delete timer', 'delete my timer', 'delete another timer', 'delete an timer',
                    'stop all my alarms', 'turn off all my alarms', 'delete all my alarms'],
        set_alarm=['alarm', 'wake me', 'timer'],
        google_home=['google home', 'googlehome'],
        jokes=['joke', 'jokes', 'make me laugh'],
        reminder=['remind', 'reminder', 'reminders'],
        distance=['far', 'distance', 'miles', 'kilometers', 'mile', 'kilometer'],
        locate_places=['where is', "where's", 'which city', 'which state', 'which country', 'which county', 'wheres'],
        directions=['take me', 'directions'],
        notes=['notes', 'note'],
        github=['git', 'github', 'clone', 'GitHub'],
        apps=['launch'],
        music=['music', 'songs', 'play', 'song'],
        faces=['face', 'recognize', 'who am i', 'detect', 'facial', 'recognition', 'detection', 'faces'],
        speed_test=['speed', 'fast'],
        brightness=['brightness', 'bright', 'dim'],
        guard_enable=['turn on security mode', 'enable security mode', 'turn on guardian mode', 'enable guardian mode'],
        guard_disable=['turn off security mode', 'disable security mode', 'turn off guardian mode',
                       'disable guardian mode'],
        flip_a_coin=['head', 'tail', 'flip', 'heads', 'tails'],
        facts=['fact', 'facts'],
        voice_changer=['voice', 'voices'],
        system_vitals=['vitals', 'statistics', 'readings', 'stats'],
        vpn_server=['vpn'],
        automation_handler=['automation'],
        background_task_handler=['background'],
        photo=['picture', 'snap', 'photo', 'pictures', 'photos'],
        version=['version'],
        simulation=['simulator', 'variation', 'simulation', 'variations'],
        sleep_control=['lock', 'screen', 'pc', 'computer'],
        sentry=['sleep', 'activate sentry mode'],
        restart_control=['restart', 'reboot'],
        shutdown=['shutdown', 'shut down', 'terminate'],
        ok=['yeah', 'yes', 'yep', 'go ahead', 'proceed', 'continue', 'carry on', 'please', 'keep going'],
        exit_=['exit', 'quit', 'no', 'nope', 'thank you', 'Xzibit', 'bye', 'good bye', 'see you later',
               'talk to you later', "that's it", 'that is it', 'never mind', 'nevermind', 'thats it'],
        kill=['kill', 'terminate yourself', 'stop running'],
        avoid=['sun', 'moon', 'mercury', 'venus', 'earth', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto',
               'a.m.', 'p.m.', 'update my to do list', 'launch', 'safari', 'body', 'human', 'centimeter', 'server',
               'cloud', 'update'],
        ngrok=['ngrok', 'public url'],
        secrets=['secret', 'secrets', 'param', 'params', 'parameter', 'parameters']
    )


if keywords:
    # Keywords for which the ' after ' split should not happen.
    ignore_after = keywords['meetings'] + keywords['avoid']
    # Keywords for which the ' and ' split should not happen.
    ignore_and = keywords['send_notification'] + keywords['reminder'] + \
        keywords['distance'] + keywords['avoid']
else:
    ignore_after, ignore_and = [], []
