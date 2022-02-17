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
   :undoc-members:

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
   :undoc-members:

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

Logger
======

.. automodule:: executors.custom_logger
   :members:
   :undoc-members:

DisplayFunctions
================

.. automodule:: executors.display_functions
   :members:
   :undoc-members:

Internet
========

.. automodule:: executors.internet
   :members:
   :undoc-members:

Location
========

.. automodule:: executors.location
   :members:
   :undoc-members:

Meetings
========

.. automodule:: executors.meetings
   :members:
   :undoc-members:

Restart
=======

.. automodule:: executors.revive
   :members:
   :undoc-members:

Robinhood
=========

.. automodule:: executors.robinhood
   :members:
   :undoc-members:

SMS
===

.. automodule:: executors.sms
   :members:
   :undoc-members:

Unconditional
=============

.. automodule:: executors.unconditional
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
   :exclude-members: greeting, capabilities, languages, what, who, form, whats_up, about_me

.. automodule:: modules.conditions.keywords
   :members:
   :exclude-members: current_date, current_time, weather, system_info, ip_info, webpage, wikipedia_, news, report, robinhood, apps, repeat, location, locate, music, gmail, meaning, create_db, add_todo, delete_todo, delete_db, todo, distance, avoid, locate_places, directions, alarm, kill_alarm, reminder, google_home, jokes, notes, github, send_sms, google_search, television, volume, face_detection, speed_test, bluetooth, brightness, lights, guard_enable, guard_disable, flip_a_coin, facts, meetings, voice_changer, system_vitals, vpn_server, personal_cloud, ok, restart_control, exit, sleep_control, kill, car, shutdown

Database
========

.. automodule:: modules.database.database
   :members:
   :undoc-members:

Face Recognition
================

.. automodule:: modules.face.facial_recognition
   :members:
   :exclude-members: cvtColor, imwrite

Lights
======

.. automodule:: modules.lights.lights
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

Personal Cloud
==============

.. automodule:: modules.personalcloud.pc_handler
   :members:
   :undoc-members:
   :exclude-members: HOME

Restart
=======

.. automodule:: restart
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
   :undoc-members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
