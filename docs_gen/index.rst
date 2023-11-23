.. Jarvis documentation master file, created by
   sphinx-quickstart on Fri Jun 11 23:27:39 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Jarvis - Voice-Activated Natural Language UI
============================================

.. toctree::
   :maxdepth: 2
   :caption: Read Me:

   README

--------Preflight Tests--------
===============================
Camera
======
.. automodule:: jarvis.modules.camera.camera
   :members:
   :undoc-members:

Audio Devices
=============
.. automodule:: jarvis.modules.peripherals
   :members:
   :exclude-members: ChannelType

====

.. autoclass:: jarvis.modules.peripherals.ChannelType(Enum)
   :members:
   :exclude-members: _generate_next_value_, _member_names_, _member_map_, _member_type_, _value2member_map_

Text To Speech
==============
.. automodule:: jarvis.modules.speaker.speak
   :members:
   :undoc-members:

Speech To Text
==============
.. automodule:: jarvis.modules.microphone.recognizer
   :members:
   :undoc-members:

Realtime Microphone Usage
=========================
.. automodule:: jarvis.modules.microphone.graph_mic
   :members:
   :undoc-members:

----------Main Module----------
===============================
Jarvis
======

.. automodule:: jarvis.main
   :members:
   :undoc-members:

Keywords Classifier
===================

.. automodule:: jarvis._preexec.keywords_handler
   :members:
   :undoc-members:

----------Jarvis API----------
==============================
API - Application
=================

.. automodule:: jarvis.api.main
   :members:
   :undoc-members:

API - Logger
============

.. automodule:: jarvis.api.logger
   :members:
   :undoc-members:

API - Server
============

.. automodule:: jarvis.api.server
   :members:
   :undoc-members:

Models - Authenticator
======================

.. automodule:: jarvis.api.models.authenticator
   :members:
   :undoc-members:

Models - Modals
===============

.. autoclass:: jarvis.api.models.modals.OfflineCommunicatorModal(pydantic.BaseModel)
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

====

.. autoclass:: jarvis.api.models.modals.StockMonitorModal(pydantic.BaseModel)
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

====

.. autoclass:: jarvis.api.models.modals.CameraIndexModal(pydantic.BaseModel)
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

====

.. autoclass:: jarvis.api.models.modals.SpeechSynthesisModal(pydantic.BaseModel)
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

Models - Settings
=================

.. autoclass:: jarvis.api.models.settings.Robinhood(pydantic.BaseModel)
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

====

.. autoclass:: jarvis.api.models.settings.Surveillance(pydantic.BaseConfig)
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

====

.. autoclass:: jarvis.api.models.settings.StockMonitor(pydantic.BaseModel)
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

====

.. automodule:: jarvis.api.models.settings.ConnectionManager
   :members:
   :undoc-members:

Routers - Basic
===============

.. automodule:: jarvis.api.routers.basics
   :members:
   :undoc-members:

Routers - FileIO
================

.. automodule:: jarvis.api.routers.fileio
   :members:
   :undoc-members:

Routers - Investment
====================

.. automodule:: jarvis.api.routers.investment
   :members:
   :undoc-members:

Routers - Offline
=================

.. automodule:: jarvis.api.routers.offline
   :members:
   :undoc-members:

Routers - SecureSend
====================

.. automodule:: jarvis.api.routers.secure_send
   :members:
   :undoc-members:

Routers - SpeechSynthesis
=========================

.. automodule:: jarvis.api.routers.speech_synthesis
   :members:
   :undoc-members:

Routers - StockMonitor
======================

.. automodule:: jarvis.api.routers.stock_monitor
   :members:
   :undoc-members:

Routers - StockAnalysis
=======================

.. automodule:: jarvis.api.routers.stock_analysis
   :members:
   :undoc-members:

Routers - Surveillance
======================

.. automodule:: jarvis.api.routers.surveillance
   :members:
   :undoc-members:

Routers - TelegramAPI
=====================

.. automodule:: jarvis.api.routers.telegram
   :members:
   :undoc-members:

Squire - Discover Routers
=========================

.. automodule:: jarvis.api.squire.discover
   :members:
   :undoc-members:

Squire - Scheduler
==================

.. automodule:: jarvis.api.squire.scheduler
   :members:
   :exclude-members: hours

Squire - StockMonitor
=====================

.. automodule:: jarvis.api.squire.stockmonitor_squire
   :members:
   :undoc-members:

Squire - StockAnalysis
======================

.. automodule:: jarvis.api.squire.stockanalysis_squire
   :members:
   :undoc-members:

Squire - Surveillance
=====================

.. automodule:: jarvis.api.squire.surveillance_squire
   :members:
   :undoc-members:

Squire - Timeout OTP
====================

.. automodule:: jarvis.api.squire.timeout_otp
   :members:
   :undoc-members:

Triggers - StockMonitor
=======================

.. automodule:: jarvis.api.triggers.stock_monitor
   :members:
   :undoc-members:

Triggers - StockReport
======================

.. automodule:: jarvis.api.triggers.stock_report
   :members:
   :undoc-members:

----------Executors----------
=============================
Alarm
=====

.. automodule:: jarvis.executors.alarm
   :members:
   :undoc-members:

Automation
==========

.. automodule:: jarvis.executors.automation
   :members:
   :undoc-members:

Background Task
===============

.. automodule:: jarvis.executors.background_task
   :members:
   :undoc-members:

Car
===

.. automodule:: jarvis.executors.car
   :members:
   :undoc-members:

Communicator
============

.. automodule:: jarvis.executors.communicator
   :members:
   :undoc-members:

Communicator Squire
===================

.. automodule:: jarvis.executors.comm_squire
   :members:
   :undoc-members:

Connection
==========

.. automodule:: jarvis.executors.connection
   :members:
   :undoc-members:

Conditions
==========

.. automodule:: jarvis.executors.conditions
   :members:
   :undoc-members:

Commander
=========

.. automodule:: jarvis.executors.commander
   :members:
   :undoc-members:

Controls
========

.. automodule:: jarvis.executors.controls
   :members:
   :undoc-members:

Crontab
=======

.. automodule:: jarvis.executors.crontab
   :members:
   :undoc-members:

Custom Conditions
=================

.. automodule:: jarvis.executors.custom_conditions
   :members:
   :undoc-members:

DateTime
========

.. automodule:: jarvis.executors.date_time
   :members:
   :undoc-members:

DisplayFunctions
================

.. automodule:: jarvis.executors.display_functions
   :members:
   :undoc-members:

Face
====

.. automodule:: jarvis.executors.face
   :members:
   :undoc-members:

Files
=====

.. automodule:: jarvis.executors.files
   :members:
   :undoc-members:

Functions
=========

.. automodule:: jarvis.executors.functions
   :members:
   :undoc-members:

GitHub
======

.. automodule:: jarvis.executors.github
   :members:
   :undoc-members:

Guard
=====

.. automodule:: jarvis.executors.guard
   :members:
   :undoc-members:

Internet
========

.. automodule:: jarvis.executors.internet
   :members:
   :undoc-members:

iOS Functions
=============

.. automodule:: jarvis.executors.ios_functions
   :members:
   :undoc-members:

Lights
======

.. automodule:: jarvis.executors.lights
   :members:
   :undoc-members:

====

.. automodule:: jarvis.executors.lights_squire
   :members:
   :undoc-members:

Listener Controls
=================

.. automodule:: jarvis.executors.listener_controls
   :members:
   :undoc-members:

Location
========

.. automodule:: jarvis.executors.location
   :members:
   :undoc-members:

Method Executor
===============

.. automodule:: jarvis.executors.method
   :members:
   :undoc-members:

MyQ Controller
==============

.. automodule:: jarvis.executors.myq_controller
   :members:
   :undoc-members:

Offline
=======

.. automodule:: jarvis.executors.offline
   :members:
   :undoc-members:

Others
======

.. automodule:: jarvis.executors.others
   :members:
   :undoc-members:

Port Handler
============

.. automodule:: jarvis.executors.port_handler
   :members:
   :undoc-members:

Processor
=========

.. automodule:: jarvis.executors.processor
   :members:
   :undoc-members:

Process Map
===========

.. automodule:: jarvis.executors.process_map
   :members:
   :undoc-members:

Remind
======

.. automodule:: jarvis.executors.remind
   :members:
   :undoc-members:

Restrictions
============

.. automodule:: jarvis.executors.restrictions
   :members:
   :undoc-members:

Robinhood
=========

.. automodule:: jarvis.executors.robinhood
   :members:
   :undoc-members:

Simulator
=========

.. automodule:: jarvis.executors.simulator
   :members:
   :undoc-members:

StaticResponses
===============

.. automodule:: jarvis.executors.static_responses
   :members:
   :undoc-members:

System
======

.. automodule:: jarvis.executors.system
   :members:
   :undoc-members:

Telegram
========

.. automodule:: jarvis.executors.telegram
   :members:
   :undoc-members:

Thermostat
==========

.. automodule:: jarvis.executors.thermostat
   :members:
   :undoc-members:

To Do
=====

.. automodule:: jarvis.executors.todo_list
   :members:
   :undoc-members:

TV
==

.. automodule:: jarvis.executors.tv
   :members:
   :undoc-members:

====

.. automodule:: jarvis.executors.tv_controls
   :members:
   :undoc-members:

Unconditional
=============

.. automodule:: jarvis.executors.unconditional
   :members:
   :undoc-members:

Volume
======

.. automodule:: jarvis.executors.volume
   :members:
   :undoc-members:

VPN Server
==========

.. automodule:: jarvis.executors.vpn_server
   :members:
   :undoc-members:

Weather
=======

.. automodule:: jarvis.executors.weather
   :members:
   :undoc-members:

====

.. automodule:: jarvis.executors.weather_monitor
   :members:
   :undoc-members:

Word Match
==========

.. automodule:: jarvis.executors.word_match
   :members:
   :undoc-members:

Wikipedia
=========

.. automodule:: jarvis.executors.wiki
   :members:
   :undoc-members:

----------Modules----------
===========================
Audio
=====

.. automodule:: jarvis.modules.audio.speaker
   :members:
   :undoc-members:

====

.. automodule:: jarvis.modules.audio.listener
   :members:
   :undoc-members:

====

.. automodule:: jarvis.modules.audio.speech_synthesis
   :members:
   :undoc-members:

====

.. automodule:: jarvis.modules.audio.tts_stt
   :members:
   :undoc-members:

====

.. automodule:: jarvis.modules.audio.voices
   :members:
   :undoc-members:

Auth Bearer
===========

.. automodule:: jarvis.modules.auth_bearer
   :members:
   :undoc-members:

Built-In Overrides
==================

.. automodule:: jarvis.modules.builtin_overrides
   :members:
   :undoc-members:

Car
===

.. automodule:: jarvis.modules.car.connector
   :members:
   :exclude-members: IFAS_BASE_URL, IFOP_BASE_URL, IF9_BASE_URL

====

.. automodule:: jarvis.modules.car.controller
   :members:
   :exclude-members: DEFAULT_CONTENT_TYPE

Conditions
==========

.. automodule:: jarvis.modules.conditions.conversation
   :members:
   :exclude-members:

====

.. automodule:: jarvis.modules.conditions.keywords
   :members:
   :exclude-members:

Crontab
=======

.. automodule:: jarvis.modules.crontab.expression
   :members:
   :exclude-members:

Classes
=======

.. automodule:: jarvis.modules.models.classes
   :members:
   :exclude-members: SupportedPlatforms, Settings, VehicleAuthorization, VehicleConnection, RecognizerSettings, TemperatureUnits, DistanceUnits, EventApp, SSQuality, BackgroundTask, EnvConfig, FileIO, Indicators

====

.. autoclass:: jarvis.modules.models.classes.SupportedPlatforms(Enum)
   :members:
   :exclude-members: _generate_next_value_, _member_names_, _member_map_, _member_type_, _value2member_map_

====

.. autoclass:: jarvis.modules.models.classes.Settings(pydantic.BaseSettings)
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

====

.. autoclass:: jarvis.modules.models.classes.VehicleAuthorization(pydantic.BaseModel)
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

====

.. autoclass:: jarvis.modules.models.classes.VehicleConnection(pydantic.BaseModel)
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

====

.. autoclass:: jarvis.modules.models.classes.RecognizerSettings(pydantic.BaseModel)
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

====

.. autoclass:: jarvis.modules.models.classes.TemperatureUnits(Enum)
   :members:
   :exclude-members: _generate_next_value_, _member_names_, _member_map_, _member_type_, _value2member_map_

====

.. autoclass:: jarvis.modules.models.classes.DistanceUnits(Enum)
   :members:
   :exclude-members: _generate_next_value_, _member_names_, _member_map_, _member_type_, _value2member_map_

====

.. autoclass:: jarvis.modules.models.classes.EventApp(Enum)
   :members:
   :exclude-members: _generate_next_value_, _member_names_, _member_map_, _member_type_, _value2member_map_

====

.. autoclass:: jarvis.modules.models.classes.SSQuality(Enum)
   :members:
   :exclude-members: _generate_next_value_, _member_names_, _member_map_, _member_type_, _value2member_map_

====

.. autoclass:: jarvis.modules.models.classes.BackgroundTask(pydantic.BaseModel)
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

====

.. autoclass:: jarvis.modules.models.classes.EnvConfig(pydantic.BaseSettings)
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

====

.. autoclass:: jarvis.modules.models.classes.FileIO(pydantic.BaseModel)
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

====

.. autoclass:: jarvis.modules.models.classes.Indicators(pydantic.BaseModel)
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

Database
========

.. automodule:: jarvis.modules.database.database
   :members:
   :undoc-members:

Exceptions
==========

.. automodule:: jarvis.modules.exceptions
   :members:
   :undoc-members:

FaceNet
=======

.. automodule:: jarvis.modules.facenet.face
   :members:
   :exclude-members: cvtColor, imwrite

Lights
======

.. automodule:: jarvis.modules.lights.smart_lights
   :members:
   :undoc-members:

====

.. automodule:: jarvis.modules.lights.preset_values
   :members:
   :undoc-members:
   :exclude-members: PRESET_VALUES

Logger
======

.. autoclass:: jarvis.modules.logger.APIConfig(pydantic.BaseModel)
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

.. autoclass:: jarvis.modules.logger.AddProcessName(logging.Filter)
   :members:
   :exclude-members:

====

.. automodule:: jarvis.modules.logger
   :members:
   :exclude-members: APIConfig, AddProcessName

Meanings
========

.. automodule:: jarvis.modules.dictionary.dictionary
   :members:
   :undoc-members:

Meetings
========

.. automodule:: jarvis.modules.meetings.ics
   :members:
   :undoc-members:

====

.. automodule:: jarvis.modules.meetings.ics_meetings
   :members:
   :undoc-members:

====

.. automodule:: jarvis.modules.meetings.events
   :members:
   :undoc-members:

Models
======

.. automodule:: jarvis.modules.models.models
   :members:
   :undoc-members:

MyQ
===

.. automodule:: jarvis.modules.myq.myq
   :members:
   :exclude-members: Operation

====

.. autoclass:: jarvis.modules.myq.myq.Operation(Enum)
   :members:
   :exclude-members: _generate_next_value_, _member_names_, _member_map_, _member_type_, _value2member_map_

Retry Handler
=============

.. automodule:: jarvis.modules.retry.retry
   :members:
   :undoc-members:

Shared Resources
================

.. automodule:: jarvis.modules.utils.shared
   :members:
   :undoc-members:

Support
=======

.. automodule:: jarvis.modules.utils.support
   :members:
   :undoc-members:

Utilities
=========

.. automodule:: jarvis.modules.utils.util
   :members:
   :undoc-members:

Telegram
========

.. automodule:: jarvis.modules.telegram.bot
   :members:
   :exclude-members: BASE_URL

====

.. automodule:: jarvis.modules.telegram.audio_handler
   :members:
   :undoc-members:

====

.. automodule:: jarvis.modules.telegram.file_handler
   :members:
   :undoc-members:

====

.. automodule:: jarvis.modules.telegram.settings
   :members:
   :exclude-members: _abc_impl, model_config, model_fields

====

.. automodule:: jarvis.modules.telegram.webhook
   :members:
   :undoc-members:

Temperature
===========

.. automodule:: jarvis.modules.temperature.temperature
   :members:
   :undoc-members:

Templates
=========

.. automodule:: jarvis.modules.templates.templates
   :members:
   :exclude-members: source, _source

Timeout
=======

.. automodule:: jarvis.modules.timeout.timeout
   :members:
   :undoc-members:

Transformer
===========

.. automodule:: jarvis.modules.transformer.gpt
   :members:
   :undoc-members:

TV Connector
============

.. automodule:: jarvis.modules.tv.lg
   :members:
   :undoc-members:

====

.. automodule:: jarvis.modules.tv.roku
   :members:
   :undoc-members:

WakeOnLAN
=========

.. automodule:: jarvis.modules.wakeonlan.wakeonlan
   :members:
   :undoc-members:

----------Test Cases----------
==============================

TestAPI
=======

.. automodule:: tests.api_test
   :members:
   :undoc-members:

TestListener
============

.. automodule:: tests.listener_test
   :members:
   :undoc-members:

TestMain
========

.. automodule:: tests.main_test
   :members:
   :undoc-members:

TestSpeaker
===========

.. automodule:: tests.speaker_test
   :members:
   :undoc-members:

TestSpeechSynthesis
===================

.. automodule:: tests.speech_synthesis_test
   :members:
   :undoc-members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
