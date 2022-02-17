import os

from modules.audio import speaker


def automation_handler(phrase: str) -> None:
    """Handles automation file resets by renaming it to tmp if requested to disable.

    Args:
        phrase: Takes the recognized phrase as an argument.
    """
    if 'enable' in phrase:
        if os.path.isfile('tmp_automation.json'):
            os.rename(src='tmp_automation.json', dst='automation.json')
            speaker.speak(text='Automation has been enabled sir!')
        elif os.path.isfile('automation.json'):
            speaker.speak(text='Automation was never disabled sir!')
        else:
            speaker.speak(text="I couldn't not find the source file to enable automation sir!")
    elif 'disable' in phrase:
        if os.path.isfile('automation.json'):
            os.rename(src='automation.json', dst='tmp_automation.json')
            speaker.speak(text='Automation has been disabled sir!')
        elif os.path.isfile('tmp_automation.json'):
            speaker.speak(text='Automation was never enabled sir!')
        else:
            speaker.speak(text="I couldn't not find the source file to disable automation sir!")
