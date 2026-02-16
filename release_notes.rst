Release Notes
=============

v7.1.2.post1 (10/14/2025)
-------------------------
- `0bcf1cd <https://github.com/thevickypedia/Jarvis/commit/0bcf1cd0c58c42781014427dcd99f9e1b61878fc>`_ chore: Release ``v7.1.2.post1``
- `2fb4d8f <https://github.com/thevickypedia/Jarvis/commit/2fb4d8fc139b7bcd5756d897bea58c9cc7a5d1ea>`_ ci: Create GH workflows to automatically upload to pypi, create a release and update release notes
- `168f58a <https://github.com/thevickypedia/Jarvis/commit/168f58a9ad9ac514ad498e232d91f30a049a6841>`_ perf: Improve error handling for IP address fetch and telegram webhook connection
- `26d9fbd <https://github.com/thevickypedia/Jarvis/commit/26d9fbdb87982eb205f38df752d2c62619ea2359>`_ perf: Consume OTP via header for robinhood report endpoint
- `67d3d98 <https://github.com/thevickypedia/Jarvis/commit/67d3d98110ee9e484d79bf75b5d3db32f51ae3fc>`_ perf: Set a max timeout when awaiting vault connection
- `ab65fe5 <https://github.com/thevickypedia/Jarvis/commit/ab65fe5a3f2d0c493b10171ea2541ff95482d9b6>`_ perf: Set API's default log level based on Jarvis' debug mode
- `4fe13fc <https://github.com/thevickypedia/Jarvis/commit/4fe13fcc5ca7367b558f088b1ab29250f2e078a9>`_ fix: Remove dead link from error response for conditional endpoints
- `5709037 <https://github.com/thevickypedia/Jarvis/commit/57090374eeee72317c160fb9e15f40df910addaa>`_ refactor: Restrict ``/listener`` endpoint to be available only on internal IPs
- `baacd0f <https://github.com/thevickypedia/Jarvis/commit/baacd0fbc45b305a6261c6c6711d024d0c0c7524>`_ refactor: Exclude integrated API endpoints from ``/docs`` handler
- `dd9a1fb <https://github.com/thevickypedia/Jarvis/commit/dd9a1fb2402b1d3f4f6c89edd11efa50760b8a45>`_ fix: Avoid first capitalized word being recognized as a place
- `27942bc <https://github.com/thevickypedia/Jarvis/commit/27942bcd162a56111057e3f8da295c0c7bb16a12>`_ dev: Update keep alive script to activate env and then trigger
- `0a0579d <https://github.com/thevickypedia/Jarvis/commit/0a0579df5ad79efcfa80dc5189920d25442c78a3>`_ ci: Bump release notes action to ``v2``
- `38c3ba0 <https://github.com/thevickypedia/Jarvis/commit/38c3ba01287ff59a823ff93b6b0b6ecb22915f23>`_ docs: Update label in README.md
- `0c73523 <https://github.com/thevickypedia/Jarvis/commit/0c735238ccbf9b57bde1852676f748fe13970b5f>`_ Update release notes

v7.1.1.post1 (07/14/2025)
-------------------------
- b400686 chore: (release) ``v7.1.1.post1``

v7.1.1 (07/14/2025)
-------------------
- 484a805 chore: (release) ``v7.1.1``
- e37bde1 docs: Include missing modules in runbook
- d38b329 dev: Validate ``autoclass`` vs `automodule`` using runbook code coverage
- 5cc715b dev: Update runbook code coverage to include inheritance check
- e698ce9 docs: Remove unconventional labels from README.md
- c89551f test: Run speaker test without speech synthesis API

v7.1.0 (07/13/2025)
-------------------
- 222d437 chore: Release `v7.1.0`
- fd0c14c feat: Allow ollama models to be hosted on external servers
- a5923de docs: Add GHA label to README.md
- 099c1f9 ci: Use reusable workflow to generate/update release notes
- 92a9b65 dev: Add a dev script to keep Jarvis running all the time
- 89d43a4 perf: Streamline the core implementation for VaultAPI integration Update runbook
- e720b67 fix: Minor bug fixes and reduce code-redundancy
- 3a67238 perf: Store table attributes for base DB in pydantic models
- 806b179 perf: Use singleton approach and re-use db instance for all modules
- 5c10e3f feat: Encrypt secrets stored locally during secure-send tranmission
- 53b9e40 fix: Fix secure-send failing due non-primitive data types on local env vars
- bee2e1a feat: Integrate spectrum UI with the backend listener status
- acb1dac fix: Fix buggy UI for listener spectrum UI
- 51f64e5 feat: Add a listener spectrum that resembles iPhone siri

v7.0.0 (06/15/2025)
-------------------
- feature: Allow speech-synthesis containers to be hosted externally and remove internal trigger
- fix: ``AVCaptureDeviceTypeExternal`` warning from ``opencv`` due to ``Continuity Camera`` in iOS
- feature: Includes an option to load env vars from ``VaultAPI``
- refactor: Restructure ollama model name and model file usage
- build (deps): Upgraded installer to improve speed and user experience with ``uv``
- build (deps): Upgraded dependencies
- refactor: Replace all API decorators with routing objects
- **Full Changelog**: https://github.com/thevickypedia/Jarvis/compare/v6.0.1...v7.0.0

v6.0.1 (06/15/2025)
-------------------
- Bug fix on openweathermap API, and occasional launch errors
- **Full Changelog**: https://github.com/thevickypedia/Jarvis/compare/v6.0.0...v6.0.1

v6.0.0 (10/04/2024)
-------------------
- Includes support for ARM based macOS machines
- Removed support for legacy macOS machines (older than High Sierra)
- Restructured installation process
- Includes a resource tracker to terminate all uncaught daemon processes
- Makes ``root_password`` optional for Linux machines
- Includes bug fixes and minor improvements to overall coding structure
- Improved container orchestration using Docker API and email templates
- **Full Changelog**: https://github.com/thevickypedia/Jarvis/compare/v5.1.0...v6.0.0

v5.1.0 (06/09/2024)
-------------------
- Includes fully operational CLI functionalities.
- Supports more than 100 repositories for GitHub account summary feature.
- Removes GitHub cloning feature by repo name.
- Bug fix on flaky screen output for terminal sessions.
- Supports ``None`` for ``startup_options`` environment variable.
- Includes endpoints to return total lines of code and total number of files as an integer or an HTML badge.

v5.0.0 (06/04/2024)
-------------------
- Includes a pre-trained generative model using Ollama
- Bug fix for Roku TV's turn on functionality
- Supports JSON and YAML files for environment variables

v4.5.1 (05/29/2024)
-------------------
- Removes `wikipedia` feature integration
- Includes break fix for an invalid return type

v4.5 (05/28/2024)
-----------------
- Includes stability improvements for IOT devices
- Improved installation experience focused to support only python 3.10 and 3.11
- Includes a new feature to host a proxy server for `GET` requests
- Onboard a new tool for notifications - `ntfy`
- Allows multiple websites for CORS origins
- Includes bug fixes and improved linting across the project
- Enables multiple notification channels for reminders
- Replaces in house module for car controls with `jlrpy`
- Includes frozen pypi packages for all supported devices

v4.4.2 (02/03/2024)
-------------------
- Bug fix on flaky response when all the lights fail to connect

v4.4.1 (02/01/2024)
-------------------
- Crash fix VPN server config and adapt to new changes
- Minor improvements in one-time passcode settings

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
- Redefines the way how alarms and reminders work
- Includes a new feature to get existing alarms
- Provides an option to choose between GPT models for OpenAI

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
