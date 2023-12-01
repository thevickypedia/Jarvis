Release Notes
=============

v4.4 (11/30/2023)
-----------------
- Removes garage feature due to `Chamberlain blockade <https://chamberlaingroup.com/press/a-message-about-our-decision-to-prevent-unauthorized-usage-of-myq>`_
- Improved failure response for light controls
- Fix bug on ``subprocess`` trigger interpreted as ``MainProcess``
- Rework dockerized ``speech-synthesis`` and desperate attempt for container logging
- Fix bug on port mapping between docker and localhost

v4.3 (11/27/2023)
-----------------
- Includes bug fixes and performance improvements
- ``wifi_connector`` now runs along side background tasks to reduce resource consumption
- ``crontab`` schedule and ``recognizer_settings`` have been moved from env vars to YAML file mapping
- More efficient logging and less unwanted information at info level logging

v4.2 (11/23/2023)
-----------------
- Includes a new feature to control `HoneyWell` thermostat
- Includes a bug fix to handle conflict with broken webhook for `TelegramAPI`
- Includes a bug fix for failed weather monitoring in background tasks

v4.0 (10/22/2023)
-----------------
- Includes a new feature to check confidence score on speech recognition
- Adds different options for ``ignore_hours`` in background tasks
- Adds an exclude/except feature when controlling ``all`` lights
- Includes more detailed response for failed lights due to unresolved hostnames
- Includes bug fix on garage controls
- Improvements in overall stability and accuracy
- Improved linting and documentation

v3.9 (10/02/2023)
-----------------
- Includes a new feature to host telegram API via webhooks
- This feature avoid long polling telegram API (pull model) and uses webhooks (push model) instead
- Improved accuracy in figuring out the light location
- Minor bug fixes when interacting with FileIO
- Improved startup time

3.7.2 (09/28/2023)
------------------
- Includes a new feature to run start up scripts
- Includes dependent module updates for startup validations

v3.7.1 (09/11/2023)
-------------------
- Includes a feature to upload any file to the server via Jarvis API or Telegram bot
- Unrecognized functions now have an offline option with stored GPT history
- Improved stability in speech recognition
- Fixes minor inconsistencies specific to volume controls on RokuTV
- Improves overall file structure

v3.7 (08/29/2023)
-----------------
- Includes a new feature to setup daily alerts for ``stock-monitor``
- Addtionally Jarvis can also list existing reminders now
- Improve overall stability and error handling for FileIO operations

v3.6 (08/22/2023)
-----------------
- Implement a feature to check for overlap in alarms
- Add a feature to get existing alarms
- Handle deletion of more than one alarms
- Remove env var for pre-commit
- Remove filtering process name for pre-commit
- Fix broken docs

v3.5.1 (08/18/2023)
-------------------
- Adds a new feature to request holidays on any date/day
- Minor improvements in stability

v3.5 (08/10/2023)
-----------------
- Adds a new feature to place functional restrictions on offline commands
- Bug fixes for TV and garage door controls
- Includes a retry logic for garage controls making it more reliable

v3.4 (07/31/2023)
-----------------
- Includes bug fixes and startup improvements
- Updates keyword mapping
- Updates to standalone test modules

v3.3 (07/28/2023)
-----------------
- Adds a feature to get all stock tickers via API
- Includes bug fixes and startup improvements

v3.2 (07/22/2023)
-----------------
- Adds a new feature to analyze stocks

v3.1.3 (07/19/2023)
-------------------
- Allow multiple tasks to run simultaneously in automation
- Allow high and low threshold for weather alerts

v3.1.2 (07/12/2023)
-------------------
- Includes bug fixes on response to failed to lights' response

v3.1.1 (07/11/2023)
-------------------
- Includes a new feature to allow ``secure-send`` via UI
- Implements a better approach to distinguish smart devices
- Minor performance and stability improvements

v3.1 (07/01/2023)
-----------------
- Includes bug fixes on vehicle connections
- Includes a new feature to set timed restarts via automation
- Improved logging for better visibility

v3.0 (06/27/2023)
-----------------
- Includes a new feature to have a custom keyword mapping
- Removes redundancy in weather alerts
- Now there is no manual intervention required to store LG tv's client key

v3.0a (05/08/2023)
------------------
- Optimized memory usage and less redundant stuff

v2.7 (05/05/2023)
-----------------
- Adds a new feature to share local env vars and AWS secrets via secure endpoint
- Reduces break time on Telegram API by introducing retry logic
- Runs all cron jobs once during startup
- Includes support for different units for temperature and distance
- Improved logging
- Includes minor bug fixes on offline commands

v2.7a (05/04/2023)
------------------
- Alpha version

2.5 (04/26/2023)
----------------
- Improved reliability and stability

2.4 (04/22/2023)
----------------
- Includes feature improvements and bug fixes on ``JarvisAPI``
- Support audio responses for multiple and timed tasks
- Includes ``speech-synthesis`` as a backup when audio driver fails
- Includes a new feature to create weather alert monitor to notify harsh weather

2.3 (04/17/2023)
----------------
- Includes a new feature to authenticate stock monitor endpoint via apikey

2.1 (04/10/2023)
----------------
- Minor bug fix for Linux OS

2.0 (04/09/2023)
----------------
- Disables security mode trigger via offline on Linux to improve stability
