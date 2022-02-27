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

API Controller
==============

.. automodule:: api.controller
   :members:
   :undoc-members:

API Server
==========

.. automodule:: api.server
   :members:
   :undoc-members:

API CronTab
===========

.. automodule:: api.cron
   :members:
   :exclude-members: COMMAND

API Log Filters
===============

.. autoclass:: api.filters.InvestmentFilter(logging.Filter)
   :members:
   :undoc-members:

Jarvis - API Models
===================

.. autoclass:: api.models.GetData(pydantic.BaseModel)
   :members:
   :undoc-members:

.. autoclass:: api.models.GetPhrase(pydantic.BaseModel)
   :members:
   :undoc-members:

.. autoclass:: api.models.LogConfig(pydantic.BaseModel)
   :members:
   :exclude-members: ACCESS_LOG_FILENAME, ACCESS_LOG_FORMAT, DEFAULT_LOG_FILENAME, DEFAULT_LOG_FORMAT, ERROR_LOG_FORMAT, LOGGING_CONFIG, LOG_LEVEL

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

Bluetooth
=========

.. automodule:: executors.bluetooth
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

Controls
========

.. automodule:: executors.controls
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

Meetings
========

.. automodule:: executors.meetings
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

Splitter
========

.. automodule:: executors.splitter
   :members:
   :undoc-members:

System
======

.. automodule:: executors.system
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

.. automodule:: modules.audio.listener
   :members:
   :undoc-members:

.. automodule:: modules.audio.voices
   :members:
   :undoc-members:

Car
===

.. automodule:: modules.car.connector
   :members:
   :exclude-members: IFAS_BASE_URL, IFOP_BASE_URL, IF9_BASE_URL

.. automodule:: modules.car.controller
   :members:
   :exclude-members: DEFAULT_CONTENT_TYPE

Conditions
==========

.. automodule:: modules.conditions.conversation
   :members:
   :exclude-members: about_me, acknowledgement, capabilities, confirmation, form, greeting, languages, wake_up1, wake_up2, wake_up3, what, whats_up, who

.. automodule:: modules.conditions.keywords
   :members:
   :exclude-members: add_todo, apps, automation, avoid, bluetooth, brightness, car, create_db, current_date, current_time, delete_db, delete_todo, directions, distance, exit_, face_detection, facts, flip_a_coin, github, google_home, google_search, guard_disable, guard_enable, ip_info, jokes, kill, kill_alarm, lights, locate, locate_places, location, meaning, meetings, music, news, notes, ok, read_gmail, reminder, repeat, report, restart_control, robinhood, send_sms, set_alarm, shutdown, sleep_control, speed_test, system_info, system_vitals, television, todo, voice_changer, volume, vpn_server, weather, wikipedia_

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

.. automodule:: modules.lights.preset_values
   :members:
   :undoc-members:
   :exclude-members: PRESET_VALUES

Local IP Scanner
================

.. automodule:: modules.netgear.ip_scanner
   :members:
   :undoc-members:

Meanings
========

.. automodule:: modules.dictionary.dictionary
   :members:
   :undoc-members:

Restart
=======

.. automodule:: restart
   :members:
   :undoc-members:

Tasks
=====

.. automodule:: modules.tasks.tasks
   :members:
   :undoc-members:

Temperature
===========

.. automodule:: modules.temperature.temperature
   :members:
   :undoc-members:

TV Connector
============

.. automodule:: modules.tv.tv_controls
   :members:
   :undoc-members:

Utils - Support
===============

.. automodule:: modules.utils.support
   :members:
   :undoc-members:

Utils - Globals
===============

.. automodule:: modules.utils.globals
   :members:
   :exclude-members: alt_gmail_pass, alt_gmail_user, birthday, car_email, car_pass, car_pin, git_pass, git_user, gmail_pass, gmail_user, home, icloud_pass, icloud_recovery, icloud_user, maps_api, meeting_app, news_api, offline_host, offline_pass, offline_port, phone_number, phrase_limit, recipient, robinhood_endpoint_auth, robinhood_pass, robinhood_qr, robinhood_user, root_password, root_user, router_pass, sensitivity, timeout, tv_client_key, vpn_password, vpn_username, weather_api, website, wolfram_api_key

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
