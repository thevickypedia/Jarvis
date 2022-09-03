.. Jarvis documentation master file, created by
   sphinx-quickstart on Fri Jun 11 23:27:39 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Jarvis's documentation!
==================================

.. toctree::
   :maxdepth: 2
   :caption: Read Me:

   README

Jarvis - Main Module
====================

.. automodule:: jarvis
   :members:
   :undoc-members:

----------Jarvis API----------
==============================
API Handler
===========

.. automodule:: api.fast
   :members:
   :undoc-members:

API Authenticator
=================

.. automodule:: api.authenticator
   :members:
   :undoc-members:

API Server
==========

.. automodule:: api.server
   :members:
   :undoc-members:

API Models
==========

.. autoclass:: api.models.GetData(pydantic.BaseModel)
   :members:
   :exclude-members:

====

.. autoclass:: api.models.InvestmentFilter(logging.Filter)
   :members:
   :exclude-members:

API Robinhood
=============

.. automodule:: api.report_gatherer
   :members:
   :undoc-members:

API Robinhood Helper
====================

.. autoclass:: api.rh_helper.CustomTemplate
   :members:
   :exclude-members: source

====

.. autoclass:: api.rh_helper.MarketHours
   :members:
   :exclude-members: hours

----------Executors----------
=============================
Alarm
=====

.. automodule:: executors.alarm
   :members:
   :undoc-members:

Automation
==========

.. automodule:: executors.automation
   :members:
   :undoc-members:

Car
===

.. automodule:: executors.car
   :members:
   :undoc-members:

Communicator
============

.. automodule:: executors.communicator
   :members:
   :undoc-members:

Conditions
==========

.. automodule:: executors.conditions
   :members:
   :undoc-members:

Commander
=========

.. automodule:: executors.commander
   :members:
   :undoc-members:

Controls
========

.. automodule:: executors.controls
   :members:
   :undoc-members:

Crontab
=======

.. automodule:: executors.crontab
   :members:
   :undoc-members:

DateTime
========

.. automodule:: executors.date_time
   :members:
   :undoc-members:

DisplayFunctions
================

.. automodule:: executors.display_functions
   :members:
   :undoc-members:

Face
====

.. automodule:: executors.face
   :members:
   :undoc-members:

Garage Door
===========

.. automodule:: executors.garage
   :members:
   :undoc-members:

GitHub
======

.. automodule:: executors.github
   :members:
   :undoc-members:

Guard
=====

.. automodule:: executors.guard
   :members:
   :undoc-members:

Internet
========

.. automodule:: executors.internet
   :members:
   :undoc-members:

Lights
======

.. automodule:: executors.lights
   :members:
   :undoc-members:

Location
========

.. automodule:: executors.location
   :members:
   :undoc-members:

Logger
======

.. automodule:: executors.logger
   :members:
   :undoc-members:

Offline
=======

.. automodule:: executors.offline
   :members:
   :undoc-members:

Others
======

.. automodule:: executors.others
   :members:
   :undoc-members:

Port Handler
============

.. automodule:: executors.port_handler
   :members:
   :undoc-members:

Processor
=========

.. automodule:: executors.processor
   :members:
   :undoc-members:

Remind
======

.. automodule:: executors.remind
   :members:
   :undoc-members:

Robinhood
=========

.. automodule:: executors.robinhood
   :members:
   :undoc-members:

System
======

.. automodule:: executors.system
   :members:
   :undoc-members:

Telegram
========

.. automodule:: executors.telegram
   :members:
   :undoc-members:

To Do
=====

.. automodule:: executors.todo_list
   :members:
   :undoc-members:

TV
==

.. automodule:: executors.tv
   :members:
   :undoc-members:

Unconditional
=============

.. automodule:: executors.unconditional
   :members:
   :undoc-members:

Volume
======

.. automodule:: executors.volume
   :members:
   :undoc-members:

VPN Server
==========

.. automodule:: executors.vpn_server
   :members:
   :undoc-members:

Weather
=======

.. automodule:: executors.weather
   :members:
   :undoc-members:

Word Match
==========

.. automodule:: executors.word_match
   :members:
   :undoc-members:

Wikipedia
=========

.. automodule:: executors.wiki
   :members:
   :undoc-members:

----------Modules----------
===========================
Audio
=====

.. automodule:: modules.audio.speaker
   :members:
   :undoc-members:

====

.. automodule:: modules.audio.listener
   :members:
   :undoc-members:

====

.. automodule:: modules.audio.speech_synthesis
   :members:
   :undoc-members:

====

.. automodule:: modules.audio.tts_stt
   :members:
   :undoc-members:

====

.. automodule:: modules.audio.voices
   :members:
   :undoc-members:

====

.. automodule:: modules.audio.win_volume
   :members:
   :undoc-members:

Car
===

.. automodule:: modules.car.connector
   :members:
   :exclude-members: IFAS_BASE_URL, IFOP_BASE_URL, IF9_BASE_URL

====

.. automodule:: modules.car.controller
   :members:
   :exclude-members: DEFAULT_CONTENT_TYPE

Conditions
==========

.. automodule:: modules.conditions.conversation
   :members:
   :exclude-members: about_me, acknowledgement, capabilities, confirmation, form, greeting, languages, wake_up1, wake_up2, wake_up3, what, whats_up, who

====

.. automodule:: modules.conditions.keywords
   :members:
   :exclude-members: add_todo, apps, automation, avoid, bluetooth, brightness, car, create_db, current_date, current_time, delete_db, delete_todo, directions, distance, exit_, face_detection, facts, flip_a_coin, github, google_home, google_search, guard_disable, guard_enable, ip_info, jokes, kill, kill_alarm, lights, locate, locate_places, location, meaning, meetings, music, news, notes, ok, read_gmail, reminder, repeat, report, restart_control, robinhood, send_sms, set_alarm, shutdown, sleep_control, speed_test, system_info, system_vitals, television, todo, voice_changer, volume, vpn_server, weather, wikipedia_

Config
======

.. autoclass:: modules.models.config.CronConfig(pydantic.BaseModel)
   :members:
   :exclude-members:

====

.. autoclass:: modules.models.config.APIConfig(pydantic.BaseModel)
   :members:
   :exclude-members:

====

.. autoclass:: modules.models.config.BotConfig(pydantic.BaseModel)
   :members:
   :exclude-members:

Crontab
=======

.. automodule:: modules.crontab.expression
   :members:
   :exclude-members:

Classes
=======

.. autoclass:: modules.models.classes.EventApp(Enum)
   :members:
   :undoc-members:

====

.. autoclass:: modules.models.classes.CustomDict(pydantic.BaseModel)
   :members:
   :undoc-members:

====

.. autoclass:: modules.models.classes.EnvConfig(pydantic.BaseSettings)
   :members:
   :undoc-members:

====

.. autoclass:: modules.models.classes.FileIO(pydantic.BaseModel)
   :members:
   :undoc-members:

====

.. autoclass:: modules.models.classes.Indicators(pydantic.BaseModel)
   :members:
   :undoc-members:

====

.. autoclass:: modules.models.classes.Settings(pydantic.BaseSettings)
   :members:
   :undoc-members:

Database
========

.. automodule:: modules.database.database
   :members:
   :undoc-members:

Exceptions
==========

.. automodule:: modules.exceptions
   :members:
   :undoc-members:

Face Recognition
================

.. automodule:: modules.face.facial_recognition
   :members:
   :exclude-members: cvtColor, imwrite

Lights
======

.. automodule:: modules.lights.smart_lights
   :members:
   :undoc-members:

====

.. automodule:: modules.lights.preset_values
   :members:
   :undoc-members:
   :exclude-members: PRESET_VALUES

Meanings
========

.. automodule:: modules.dictionary.dictionary
   :members:
   :undoc-members:

Meetings
========

.. automodule:: modules.meetings.events
   :members:
   :undoc-members:

====

.. automodule:: modules.meetings.icalendar
   :members:
   :undoc-members:

Models
======

.. autoclass:: modules.models.models
   :members:
   :undoc-members:

MyQ
===

.. autoclass:: modules.myq.myq.Operation(Enum)
   :members:
   :undoc-members:

.. autoclass:: modules.myq.myq.garage_controller
   :members:
   :undoc-members:

Offline
=======

.. automodule:: modules.offline.compatibles
   :members:
   :undoc-members:

Retry Handler
=============

.. automodule:: modules.retry.retry
   :members:
   :undoc-members:

Repeated Timer
==============

.. automodule:: modules.timer.executor
   :members:
   :undoc-members:

Shared Resources
================

.. automodule:: modules.utils.shared
   :members:
   :undoc-members:

Support
=======

.. automodule:: modules.utils.support
   :members:
   :undoc-members:

Telegram
========

.. automodule:: modules.telegram.bot
   :members:
   :exclude-members: BASE_URL

====

.. automodule:: modules.telegram.audio_handler
   :members:
   :undoc-members:

Temperature
===========

.. automodule:: modules.temperature.temperature
   :members:
   :undoc-members:

Timeout
=======

.. automodule:: modules.timeout.timeout
   :members:
   :undoc-members:

====

.. automodule:: modules.timeout.responder
   :members:
   :undoc-members:

TV Connector
============

.. automodule:: modules.tv.tv_controls
   :members:
   :undoc-members:

WakeOnLAN
=========

.. automodule:: modules.wakeonlan.wakeonlan
   :members:
   :undoc-members:


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
