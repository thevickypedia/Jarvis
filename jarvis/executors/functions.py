# noinspection PyUnresolvedReferences
"""Creates a dictionary with the keyword category as key and the function to be called as value.

>>> Functions

"""

from collections import OrderedDict
from typing import Callable

from jarvis.executors import (alarm, automation, background_task, car,
                              comm_squire, communicator, controls, date_time,
                              display_functions, face, github, guard, internet,
                              ios_functions, lights, listener_controls,
                              location, myq_controller, others, remind,
                              robinhood, simulator, static_responses, system,
                              todo_list, tv, volume, vpn_server, weather, wiki)
from jarvis.modules.audio import voices
from jarvis.modules.meetings import events, ics_meetings


def function_mapping() -> OrderedDict[str, Callable]:
    """Returns an ordered dictionary of functions mapping.

    Returns:
        OrderedDict:
        OrderedDict of category and keywords as key-value pairs.
    """
    return OrderedDict(
        listener_control=listener_controls.listener_control,
        send_notification=comm_squire.send_notification,
        lights=lights.lights,
        television=tv.television,
        volume=volume.volume,
        car=car.car,
        garage=myq_controller.garage,
        weather=weather.weather,
        meetings=ics_meetings.meetings,
        events=events.events,
        current_date=date_time.current_date,
        current_time=date_time.current_time,
        system_info=system.system_info,
        ip_info=internet.ip_info,
        wikipedia_=wiki.wikipedia_,
        news=others.news,
        report=others.report,
        robinhood=robinhood.robinhood,
        repeat=others.repeat,
        location=location.location,
        locate=ios_functions.locate,
        read_gmail=communicator.read_gmail,
        meaning=others.meaning,
        todo=todo_list.todo,
        kill_alarm=alarm.kill_alarm,
        set_alarm=alarm.set_alarm,
        google_home=others.google_home,
        jokes=others.jokes,
        reminder=remind.reminder,
        distance=location.distance,
        locate_places=location.locate_places,
        directions=location.directions,
        notes=others.notes,
        github=github.github,
        apps=others.apps,
        music=others.music,
        faces=face.faces,
        speed_test=internet.speed_test,
        brightness=display_functions.brightness,
        guard_enable=guard.guard_enable,
        guard_disable=guard.guard_disable,
        flip_a_coin=others.flip_a_coin,
        facts=others.facts,
        voice_changer=voices.voice_changer,
        system_vitals=system.system_vitals,
        vpn_server=vpn_server.vpn_server,
        automation_handler=automation.automation_handler,
        background_task_handler=background_task.background_task_handler,
        photo=others.photo,
        version=others.version,
        simulation=simulator.simulation,
        sleep_control=controls.sleep_control,
        sentry=controls.sentry,
        restart_control=controls.restart_control,
        shutdown=controls.shutdown,
        kill=controls.kill,
        greeting=static_responses.greeting,
        capabilities=static_responses.capabilities,
        languages=static_responses.languages,
        what=static_responses.what,
        who=static_responses.who,
        age=static_responses.age,
        form=static_responses.form,
        whats_up=static_responses.whats_up,
        about_me=static_responses.about_me
    )
