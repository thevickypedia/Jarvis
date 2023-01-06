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

--------Preflight Tests--------
===============================
Camera
======
.. automodule:: modules.camera.camera
   :members:
   :undoc-members:

Audio Devices
=============
.. automodule:: modules.peripherals
   :members:
   :undoc-members:

Text To Speech
==============
.. automodule:: modules.speaker.speak
   :members:
   :undoc-members:

Speech To Text
==============
.. automodule:: modules.microphone.recognizer
   :members:
   :undoc-members:

----------Main Module----------
===============================
Jarvis
======

.. automodule:: jarvis
   :members:
   :undoc-members:

Keywords Classifier
===================

.. automodule:: _preexec.keywords_handler
   :members:
   :undoc-members:

----------Jarvis API----------
==============================
API - Application
=================

.. automodule:: api.fast
   :members:
   :undoc-members:

API - Server
============

.. automodule:: api.server
   :members:
   :undoc-members:

Modals - Authenticator
======================

.. automodule:: api.modals.authenticator
   :members:
   :undoc-members:

Modals - Models
===============

.. autoclass:: api.modals.models.OfflineCommunicatorModal(pydantic.BaseModel)
   :members:
   :exclude-members:

====

.. autoclass:: api.modals.models.StockMonitorModal(pydantic.BaseModel)
   :members:
   :exclude-members:

====

.. autoclass:: api.modals.models.CameraIndexModal(pydantic.BaseModel)
   :members:
   :exclude-members:

====

.. autoclass:: api.modals.models.SpeechSynthesisModal(pydantic.BaseModel)
   :members:
   :exclude-members:

Modals - Settings
=================

.. autoclass:: api.modals.settings.Robinhood(pydantic.BaseModel)
   :members:
   :undoc-members:

====

.. autoclass:: api.modals.settings.Surveillance(pydantic.BaseConfig)
   :members:
   :undoc-members:

====

.. autoclass:: api.modals.settings.StockMonitor(pydantic.BaseModel)
   :members:
   :undoc-members:

====

.. automodule:: api.modals.settings.ConnectionManager
   :members:
   :undoc-members:

Routers - Basic
===============

.. automodule:: api.routers.basics
   :members:
   :undoc-members:

Routers - FileIO
================

.. automodule:: api.routers.fileio
   :members:
   :undoc-members:

Routers - Helper
================

.. automodule:: api.routers.helper
   :members:
   :undoc-members:

Routers - Investment
====================

.. automodule:: api.routers.investment
   :members:
   :undoc-members:

Routers - Offline
=================

.. automodule:: api.routers.offline
   :members:
   :undoc-members:

Routers - SpeechSynthesis
=========================

.. automodule:: api.routers.speech_synthesis
   :members:
   :undoc-members:

Routers - StockMonitor
======================

.. automodule:: api.routers.stock_monitor
   :members:
   :undoc-members:

Routers - Surveillance
======================

.. automodule:: api.routers.surveillance
   :members:
   :undoc-members:

Squire - Logger
===============

.. automodule:: api.squire.logger
   :members:
   :undoc-members:

Squire - Scheduler
==================

.. automodule:: api.squire.scheduler.MarketHours
   :members:
   :exclude-members: hours

.. automodule:: api.squire.scheduler.rh_cron_schedule
   :members:
   :exclude-members:

.. automodule:: api.squire.scheduler.sm_cron_schedule
   :members:
   :exclude-members:

Squire - StockMonitor
=====================

.. automodule:: api.squire.stockmonitor_squire
   :members:
   :undoc-members:

Squire - Surveillance
=====================

.. automodule:: api.squire.surveillance_squire
   :members:
   :undoc-members:

Squire - Timeout OTP
====================

.. automodule:: api.squire.timeout_otp
   :members:
   :undoc-members:

Triggers - StockMonitor
=======================

.. automodule:: api.triggers.stock_monitor
   :members:
   :undoc-members:

Triggers - StockReport
======================

.. automodule:: api.triggers.stock_report
   :members:
   :undoc-members:

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

Background Tasks
================

.. automodule:: executors.background_tasks
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

Communicator Squire
===================

.. automodule:: executors.comm_squire
   :members:
   :undoc-members:

Connection
==========

.. automodule:: executors.connection
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

.. automodule:: executors.myq_controller
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

iOS Functions
=============

.. automodule:: executors.ios_functions
   :members:
   :undoc-members:

Lights
======

.. automodule:: executors.lights
   :members:
   :undoc-members:

Lights Squire
=============

.. automodule:: executors.lights_squire
   :members:
   :undoc-members:

Location
========

.. automodule:: executors.location
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

====

.. automodule:: executors.tv_controls
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

Auth Bearer
===========

.. automodule:: modules.auth_bearer
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
   :exclude-members:

====

.. automodule:: modules.conditions.keywords
   :members:
   :exclude-members:

====

.. automodule:: modules.conditions.keywords_base
   :members:
   :exclude-members:

Crontab
=======

.. automodule:: modules.crontab.expression
   :members:
   :exclude-members:

Classes
=======

.. autoclass:: modules.models.classes.Settings(pydantic.BaseSettings)
   :members:
   :undoc-members:

====

.. autoclass:: modules.models.classes.EventApp(Enum)
   :members:
   :undoc-members:

====

.. autoclass:: modules.models.classes.Sensitivity(Enum)
   :members:
   :undoc-members:

====

.. autoclass:: modules.models.classes.RecognizerSettings(pydantic.BaseSettings)
   :members:
   :undoc-members:

====

.. autoclass:: modules.models.classes.SSQuality(Enum)
   :members:
   :undoc-members:

====

.. autoclass:: modules.models.classes.BackgroundTask(pydantic.BaseModel)
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

FaceNet
=======

.. automodule:: modules.facenet.face
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

Logger
======
.. automodule:: modules.logger.custom_logger
   :members:
   :exclude-members:

Config
======

.. autoclass:: modules.logger.config.APIConfig(pydantic.BaseModel)
   :members:
   :exclude-members:

.. autoclass:: modules.logger.config.AddProcessName(logging.Filter)
   :members:
   :exclude-members:

.. automodule:: modules.logger.config.multiprocessing_logger
   :members:
   :exclude-members:

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

.. automodule:: modules.models.models
   :members:
   :undoc-members:

MyQ
===

.. automodule:: modules.myq.myq
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

Utilities
=========

.. automodule:: modules.utils.util
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

Templates
=========

.. automodule:: modules.templates.templates
   :members:
   :exclude-members: source, _source

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

.. automodule:: modules.tv.lg
   :members:
   :undoc-members:

====

.. automodule:: modules.tv.roku
   :members:
   :undoc-members:

WakeOnLAN
=========

.. automodule:: modules.wakeonlan.wakeonlan
   :members:
   :undoc-members:

Wi-Fi Connector
===============

.. automodule:: modules.wifi.connector
   :members:
   :undoc-members:

Windows
=======

.. automodule:: modules.windows.win_notifications
   :members:
   :undoc-members:

====

.. automodule:: modules.windows.win_volume
   :members:
   :undoc-members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
