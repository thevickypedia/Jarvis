Release Notes
=============

v8.0.0a0 (02/15/2026)
---------------------
- `9581728 <https://github.com/thevickypedia/Jarvis/commit/958172838afe6d419d470b4bb084232d4efd63ad>`_ chore: Release ``v8.0.0a0``
- `438fe26 <https://github.com/thevickypedia/Jarvis/commit/438fe2653eb2d8f6c1c382deb57c72e5554c681c>`_ refactor: Improve reusability across robinhood on-demand vs scheduled summary
- `9f70b53 <https://github.com/thevickypedia/Jarvis/commit/9f70b5341cfdd9e7e52d0ee04fdf7c51095cdbcf>`_ fix: Replace ``pyrh`` with ``robin_stocks`` to get portfolio information
- `53524ae <https://github.com/thevickypedia/Jarvis/commit/53524aed591f1644494ef086537edddb2eb715ba>`_ fix: Include an exception handler when retrieving terminal size
- `9c2d94f <https://github.com/thevickypedia/Jarvis/commit/9c2d94f723ac0b990477b945a8110b7bdcfe3f1a>`_ fix: Update dev scripts to handle versions with extra decimals and invalid version
- `d582fe5 <https://github.com/thevickypedia/Jarvis/commit/d582fe5d5306a5b9f46f6b17858bea5adf87da4b>`_ perf: Increase caching age for line of code and number of files functions
- `3acce6f <https://github.com/thevickypedia/Jarvis/commit/3acce6fc36302d4cedc6d37b2cb62fba2180ff6c>`_ fix: Resolve a bug in the stock analysis - ticker gatherer
- `1fc665a <https://github.com/thevickypedia/Jarvis/commit/1fc665aabbdae222bf229d681524a73f37d35d7f>`_ perf: Replace retry logic for ``stopper`` table with a controlled loop with exception handlers
- `56455b9 <https://github.com/thevickypedia/Jarvis/commit/56455b9170ac42caa767c675f3d6db734ecac0dc>`_ perf: Upgrade possible dependencies and improve build stability
- `c94f8f8 <https://github.com/thevickypedia/Jarvis/commit/c94f8f84810f1bf458b7196ed3231fbc07023dea>`_ perf: Remove proxy service feature to improve security
- `c76a683 <https://github.com/thevickypedia/Jarvis/commit/c76a6834054760ae659c44f58f2f58ed63fdfb78>`_ fix: Ensure main process doesn't crash due to DB errors
- `82bb5cf <https://github.com/thevickypedia/Jarvis/commit/82bb5cf1d2f67ab79b7b8ba4478679823bf10f4e>`_ perf: Replace self restart for background task with a task shutdown action
- `2161dfd <https://github.com/thevickypedia/Jarvis/commit/2161dfd64f684512f28a8ec3d04afd8e8d071eab>`_ feat: Include self restart functionality when background tasks fail repeatedly
- `e6bac1f <https://github.com/thevickypedia/Jarvis/commit/e6bac1fd72f2236b148596e9f20e42afd8345714>`_ fix: Avoid ``TypeError`` when joining Ntfy url and topic
- `dec4d99 <https://github.com/thevickypedia/Jarvis/commit/dec4d993c2ab1aebef4104aecf433d43e63eae39>`_ feat: Notify user when a background task or telegram polling crashes
- `1cc59fa <https://github.com/thevickypedia/Jarvis/commit/1cc59fa197ef4870d60e0cd7a3f86c8b2a628138>`_ refactor: Remove redundant checks for username and password for notification service
- `4847f9b <https://github.com/thevickypedia/Jarvis/commit/4847f9be3ff170764724362b5d433fce9733b218>`_ refactor: Add a helper function to create async tasks with callback attached
- `9507efd <https://github.com/thevickypedia/Jarvis/commit/9507efdc315a27343df8b7eb4c7b0b1ea2fe039f>`_ perf: Implement a tracking mechanism for async tasks with automatic restarts and notifications
- `485d67c <https://github.com/thevickypedia/Jarvis/commit/485d67c625e75b65b2f128f06a11f1f150942d02>`_ fix: Shutdown background tasks gracefully with ``SIGTERM`` before sending ``SIGKILL`` with a timeout
- `2a6f306 <https://github.com/thevickypedia/Jarvis/commit/2a6f306d03ec57c51f7f315fd7e18f4d16d2eec0>`_ docs: Update runbook
- `0916466 <https://github.com/thevickypedia/Jarvis/commit/091646668be5bfe27b06946903be6f6ff4eea5e4>`_ perf: Re-use existing response from GPT history for identical requests by default
- `9783c11 <https://github.com/thevickypedia/Jarvis/commit/9783c1188615f011f663d99c478ff88e9e97a91c>`_ docs: Update runbook
- `d827e25 <https://github.com/thevickypedia/Jarvis/commit/d827e2583b0ebbbbe5fec27d0a7de7aa9213b636>`_ fix: Avoid ``AttributeError`` in a thread when ``gpt_history.yaml`` file does not exist
- `0e745d7 <https://github.com/thevickypedia/Jarvis/commit/0e745d77ce89e898b56930f8430ff267d21baba8>`_ fix: Add singular form for ``get`` AWS SSM params
- `ec39f90 <https://github.com/thevickypedia/Jarvis/commit/ec39f9070db8ce7ccfe0f82cd623a13ea7eb8b94>`_ refactor: Remove the use of ``Modelfile`` and use the client to create custom model with parameters for GPT
- `c163de9 <https://github.com/thevickypedia/Jarvis/commit/c163de9246dca0096581ef05d8596e430f4a4fd0>`_ perf: Improve instructions to GPT models
- `5b9377d <https://github.com/thevickypedia/Jarvis/commit/5b9377d57db782abec4eff49575b779687c79531>`_ perf: Remove dictionary feature and let GPT handle it as part of fallback
- `775c72a <https://github.com/thevickypedia/Jarvis/commit/775c72aa464cbfce4c2556b795c1151bcc940d7f>`_ lint: Resolve all warnings from ``Pylance``
- `6038f5d <https://github.com/thevickypedia/Jarvis/commit/6038f5d5d6ece26a5631da071f3b134874a00a14>`_ fix: Handle unlimited task distribution for long polling in background tasks
- `c28042e <https://github.com/thevickypedia/Jarvis/commit/c28042ed7e02be2a59f6f82f562b7aae30121db6>`_ perf: Setup self-restart ability for telegram polling and remove un-awaited restart loop
- `25c2d6e <https://github.com/thevickypedia/Jarvis/commit/25c2d6e5c8ed18e0d56f12e53b331dae51b42ef2>`_ refactor: Move telegram specific code to a dedicated module
- `526c416 <https://github.com/thevickypedia/Jarvis/commit/526c4168adcbd26440d64c1c94298a9b4ad7eb83>`_ perf: Shorten ttl for telegram polling and remove ``dry_run`` flag for bg tasks
- `5d0585f <https://github.com/thevickypedia/Jarvis/commit/5d0585f82b7e5086b8bd935ca95d10461f04d517>`_ docs: Update runbook
- `ce7afc5 <https://github.com/thevickypedia/Jarvis/commit/ce7afc5bacc5d694b73f7968b692d5e6656ec085>`_ lint: Update line limit for ``black`` in ``pre-commit``
- `054cc83 <https://github.com/thevickypedia/Jarvis/commit/054cc83e4698d455925099501fd431e23bc6b967>`_ perf: Remove top-level overhead for Wi-Fi connection
- `60ac596 <https://github.com/thevickypedia/Jarvis/commit/60ac5962b0a4987c466031d0bbaf51179c304e81>`_ perf: Remove awaiting Wi-Fi checker in background tasks
- `f880d52 <https://github.com/thevickypedia/Jarvis/commit/f880d52ac5111608e5b39175566559e832b58688>`_ perf: Move each executor from background tasks to an async task
- `23df534 <https://github.com/thevickypedia/Jarvis/commit/23df534722e6b591d29648f938f43f81cf58a9ff>`_ refactor: Move all things background tasks into the api module
- `06c4f06 <https://github.com/thevickypedia/Jarvis/commit/06c4f06c54599da9a365ecba855b05f7cf7592e1>`_ perf: Integrate fallback telegram polling into background task
- `e9be43f <https://github.com/thevickypedia/Jarvis/commit/e9be43f8d33d34fc2e3afe6b41f823161e31b368>`_ perf: Switch distance context for offline vs voice interactions
- `e34d8e3 <https://github.com/thevickypedia/Jarvis/commit/e34d8e3edd41442e77195a537a167ac303bb2613>`_ docs: Update runbook
- `4c8ddef <https://github.com/thevickypedia/Jarvis/commit/4c8ddef3c6274f77dea7898155c4c0b0700460ec>`_ fix: Rename ``executors.connection`` to ``executors.connectivity`` to avoid module naming conflict
- `2b19364 <https://github.com/thevickypedia/Jarvis/commit/2b1936482000a9368edd2adde6b194e8618bdc9c>`_ perf: Replace dedicated process for background tasks with asyncio
- `730899c <https://github.com/thevickypedia/Jarvis/commit/730899cebba0ab550872eb34d631197d82110680>`_ docs: Update runbook
- `c22716c <https://github.com/thevickypedia/Jarvis/commit/c22716ccfb5da2306f454185c5f00c15dc06a032>`_ refactor: Remove car integration
- `f55b30b <https://github.com/thevickypedia/Jarvis/commit/f55b30bfe1faaa60d0c90a0f750da2a5328a5eca>`_ docs: Update runbook
- `b5914fe <https://github.com/thevickypedia/Jarvis/commit/b5914fec153a853e44b34e9a8d63b6606e07da1f>`_ refactor: Remove simulation feature
- `8d3934a <https://github.com/thevickypedia/Jarvis/commit/8d3934a676e7de814382ae56e50b8d4858d15df7>`_ docs: Update runbook
- `e613feb <https://github.com/thevickypedia/Jarvis/commit/e613feb07cdc02aae69a467929820294890107fa>`_ perf: Upgrade ``sphinx`` version
- `2677749 <https://github.com/thevickypedia/Jarvis/commit/2677749a361e83fd68f928faad815bbe7123955a>`_ refactor: Remove ``vpn-server`` integration
- `5292a5e <https://github.com/thevickypedia/Jarvis/commit/5292a5eec1e1cb90b9a84ea5688ffb95abb887ae>`_ fix: Handle missing ``face_recognition`` module due to issues with ``dlib``
- `1120a65 <https://github.com/thevickypedia/Jarvis/commit/1120a65287f08410b86704b926339aab350993d6>`_ feat: Update keyword mapping to apply the same settings for tv and projector
- `a504f0a <https://github.com/thevickypedia/Jarvis/commit/a504f0a02003e88355e4f5a5cd4e209e1be7e05a>`_ fix: Avoid URL parse error when using an external Ollama server
- `70d733a <https://github.com/thevickypedia/Jarvis/commit/70d733a2a4306cd306caf78e4ca46e30083ac888>`_ refactor: Replace all hard coded process names with enums
- `83243f1 <https://github.com/thevickypedia/Jarvis/commit/83243f138afe3458ac11b63b4c35fd0a9a632761>`_ docs: Update runbook
- `dec38fe <https://github.com/thevickypedia/Jarvis/commit/dec38fe8617f493b42e35c267f22bc5daaea8d0f>`_ fix: Avoid startup errors for GPT instance and improve error handling
- `02e7596 <https://github.com/thevickypedia/Jarvis/commit/02e759621fa19a1701031e4e26ce90e49d4079df>`_ refactor: Parse HTML response from ICS calendar request before logging
- `542e867 <https://github.com/thevickypedia/Jarvis/commit/542e867ecc2196383136d9ddc3b323a5cd4f5b89>`_ perf: Remove ``__pycache__`` deletion during startup
- `ce6f0b2 <https://github.com/thevickypedia/Jarvis/commit/ce6f0b27c355d6d4cd48b5f08f5e8f5c2f5b267b>`_ chore: Update release notes for v7.1.2.post1

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
