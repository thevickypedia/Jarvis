from modules.conditions import conversation, keywords


def offline_compatible() -> list:
    """Calls ``Keywords`` and ``Conversation`` classes to get the variables that are compatible.

    See Also:
        - ``offline_communicator`` cannot process commands that require an interaction with the user.
        - This is because ``audio_driver.stop()`` will stop the ``audio_driver.runAndWait()`` in an interaction.
        - This action will raise a ``RuntimeError`` since the ``audio_driver.endLoop()`` would have already started.

    Returns:
        list:
        Flat list from a matrix (list of lists) after removing the duplicates.
    """
    offline_words = [keywords.sleep_control,
                     keywords.exit_,
                     keywords.set_alarm,
                     keywords.current_time,
                     keywords.apps,
                     keywords.distance,
                     keywords.face_detection,
                     keywords.facts,
                     keywords.weather,
                     keywords.flip_a_coin,
                     keywords.jokes,
                     keywords.todo,
                     keywords.locate_places,
                     keywords.read_gmail,
                     keywords.google_home,
                     keywords.guard_enable,
                     keywords.guard_disable,
                     keywords.lights,
                     keywords.robinhood,
                     keywords.current_date,
                     keywords.ip_info,
                     keywords.brightness,
                     keywords.news,
                     keywords.location,
                     keywords.vpn_server,
                     keywords.reminder,
                     keywords.system_info,
                     keywords.system_vitals,
                     keywords.volume,
                     keywords.meaning,
                     keywords.meetings,
                     keywords.events,
                     keywords.car,
                     keywords.television,
                     keywords.automation,
                     conversation.about_me,
                     conversation.capabilities,
                     conversation.form,
                     conversation.greeting,
                     conversation.languages,
                     conversation.what,
                     conversation.whats_up,
                     conversation.who]
    matrix_to_list = sum(offline_words, []) or [item for sublist in offline_words for item in sublist]
    return [i.strip() for n, i in enumerate(matrix_to_list) if i not in matrix_to_list[n + 1:]]  # remove dupes
