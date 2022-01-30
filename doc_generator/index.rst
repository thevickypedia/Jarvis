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

Jarvis - API Handler
====================

.. automodule:: api.fast
   :members:
   :undoc-members:

Jarvis - API CronTab
====================

.. automodule:: api.cron
   :members:
   :undoc-members:

Jarvis - API Controller
=======================

.. automodule:: api.controller
   :members:
   :undoc-members:

Jarvis - API Log Filters
========================

.. autoclass:: api.filters.EndpointFilter(logging.Filter)
   :members:
   :undoc-members:

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

Jarvis - API Robinhood
======================

.. automodule:: api.report_gatherer
   :members:
   :undoc-members:

Jarvis - API Robinhood Helper
=============================

.. autoclass:: api.rh_helper.CustomTemplate
   :members:
   :undoc-members:
   :exclude-members: source

.. autoclass:: api.rh_helper.MarketHours
   :members:
   :undoc-members:
   :exclude-members: hours

Car - Connector Module
======================

.. automodule:: helper_functions.car_connector
   :members:
   :undoc-members:
   :exclude-members: IFAS_BASE_URL, IFOP_BASE_URL, IF9_BASE_URL

Car - Controller Module
=======================

.. automodule:: helper_functions.car_controller
   :members:
   :undoc-members:
   :exclude-members: DEFAULT_CONTENT_TYPE

Conversation
============

.. automodule:: helper_functions.conversation
   :members:
   :undoc-members:
   :exclude-members: greeting, capabilities, languages, what, who, form, whats_up, about_me

Database
========

.. automodule:: helper_functions.database
   :members:
   :undoc-members:

Face Recognition
================

.. automodule:: helper_functions.facial_recognition
   :members:
   :exclude-members: cvtColor, imwrite

Keywords
========

.. automodule:: helper_functions.keywords
   :members:
   :undoc-members:
   :exclude-members: current_date, current_time, weather, system_info, ip_info, webpage, wikipedia_, news, report, robinhood, apps, repeat, location, locate, music, gmail, meaning, create_db, add_todo, delete_todo, delete_db, todo, distance, avoid, locate_places, directions, alarm, kill_alarm, reminder, google_home, jokes, notes, github, send_sms, google_search, television, volume, face_detection, speed_test, bluetooth, brightness, lights, guard_enable, guard_disable, flip_a_coin, facts, meetings, voice_changer, system_vitals, vpn_server, personal_cloud, ok, restart_control, exit, sleep_control, kill, shutdown

Lights
======

.. automodule:: helper_functions.lights
   :members:
   :undoc-members:

.. automodule:: helper_functions.preset_values
   :members:
   :undoc-members:

Local IP Scanner
================

.. automodule:: helper_functions.ip_scanner
   :members:
   :undoc-members:

Logger
======

.. automodule:: helper_functions.logger
   :members:
   :undoc-members:

SMS Notification
================

.. automodule:: helper_functions.notify
   :members:
   :undoc-members:

Personal Cloud
==============

.. automodule:: helper_functions.personal_cloud
   :members:
   :undoc-members:
   :exclude-members: HOME

Robinhood Gatherer
==================

.. automodule:: helper_functions.robinhood
   :members:
   :undoc-members:

Temperature
===========

.. automodule:: helper_functions.temperature
   :members:
   :undoc-members:

TV Connector
============

.. automodule:: helper_functions.tv_controls
   :members:
   :undoc-members:

Restart
=======

.. automodule:: restart
   :members:
   :undoc-members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
