Release Notes
=============

v6.0.0 (10/04/2024)
-------------------
- Release `v6.0.0`

v5.1.0 (06/09/2024)
-------------------
- Release `v5.1.0`

v5.0.0 (06/04/2024)
-------------------
- Release `v5.0.0`

v4.5.1 (05/29/2024)
-------------------
- Remove `wikipedia` feature integration
- Fix bug on invalid return type
- Release micro version

v4.5 (05/28/2024)
-----------------
- Release `v4.5`
- Upgrade GH actions for `none-shall-pass` and `pypi-publish`

v4.4.2 (02/03/2024)
-------------------
- Release `v4.4.2`

v4.4.1 (02/01/2024)
-------------------
- Release `v4.4.1`

v4.4 (11/30/2023)
-----------------
- Release `v4.4`

v4.3 (11/27/2023)
-----------------
- Release `v4.3`

v4.2 (11/23/2023)
-----------------
- Release `v4.2`

v4.0 (10/22/2023)
-----------------
- Update dependencies on pyproject.toml

v3.9 (10/02/2023)
-----------------
- Release `v3.9`
- Remove unnecessary thread binding for audio driver
- Redo imports during startup

3.7.2 (09/28/2023)
------------------
- Release `v3.7.2`

v3.7.1 (09/11/2023)
-------------------
- Release v3.7.1

v3.7 (08/29/2023)
-----------------
- Release version 3.7

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
- Use ``block-stdout`` to block print statements
- Re-use ``inspect.engine()`` element from support.py
- Add a feature to get holidays in any country at any time
- Update dependencies in version_locked_requirements.txt

v3.5 (08/10/2023)
-----------------
- Onboard `gitverse` for release notes
- Allow retry module to accept multiple exceptions
- Implement retry logic for garage door controls
- Fix inconsistencies in shutting down LG TV
- Fix frequently used commands' storage
- Resort keywords.py
- Enable restart processes via offline communicators
- Remove stripping special characters for offline commands
- Remove unused arguments

v3.4 (07/31/2023)
-----------------
- Change response for ``ChatGPT``'s failed authentication
- Fix secret access via offline communicator

v3.3 (07/28/2023)
-----------------
- Brute force ``timeout`` on ``ChatGPT`` instance creation
- Fix some random start up errors and delays
- Create an option to get stock tickers as a dict
- Update docs page for API endpoint
- Release v3.3

v3.2 (07/22/2023)
-----------------
- Implement a new feature to analyze stocks
- Remove unwanted ticker gathering methods
- Release version 3.2

v3.1.3 (07/19/2023)
-------------------
- Multiple tasks to run simultaneously in automation
- Add low and high threshold for weather alerts
- Update README.md and bump sub-version

v3.1.2 (07/12/2023)
-------------------
- Fix flaky response for failed lights

v3.1.1 (07/11/2023)
-------------------
- Allow ``secure-send`` to work via UI
- Better way to distinguish smart devices
- Reduce redundancy and re-use variables
- Add more keywords for secure send
- Update CORS allowance for headers
- Update README.md and type hints
- Bump version

v3.1 (07/01/2023)
-----------------
- Fix flaky connection reset in car module
- Allow restart via ``automation.yaml``
- Log vehicle auth expiration
- Fix missing hosted device information in logs
- Add inline comments
- Instantiate vehicle objects

v3.0 (06/27/2023)
-----------------
- Enable custom keywords to functions mapping
- Remove redundancy in weather alert trigger
- Set weather alert trigger via background tasks
- Keep weather alert time format consistent
- Add an option to manually enable the listener
- Add automation and smart devices to files.py
- Cleanup keywords_handler.py
- Rename timeout and phrase_limit to more sensible ones
- Auto store LG tv's client key in smart_devices.yaml

v3.0a (05/08/2023)
------------------
- Optimize memory usage and remove globals
- Reduce top level variable declarations
- Create function mapping dict in place of globals
- Reuse stock report for robinhood summarization

v2.7 (05/05/2023)
-----------------
- Fix inconsistent offline compatibles
- Remove todo for NLTK since compute time is high

v2.7a (05/04/2023)
------------------
- Create a feature to send env vars/secrets securely
- Create a retry logic in TelegramAPI for parsing errors
- Kick off all cron jobs during startup
- Fix a bug in location request failing for offline process
- Support different units for temperature and distance
- Add *args to functions associated to conditions
- Avoid converting to dict for APIResponse
- Convert Thread to Timer for reset OTPs
- Remove revaluation of CronExpression
- Change headers to use hyphen instead of underscore
- Add more logging towards unrecognized models
- Add todos for next release
- Update .gitignore and docs
- Release alpha version

2.5 (04/26/2023)
----------------
- Run `py3-tts` test on current python `bin`
- Run pre-checks on meetings in background tasks

2.4 (04/22/2023)
----------------
- Feature improvements and bug fixes on `JarvisAPI`
- Support audio responses for multiple and timed tasks
- Exhaust all audio options before returning string
- Resolve edge case scenario in pyttsx3
- Enable speech-synthesis if audio driver fails
- Create weather alert monitor to notify harsh weather
- Remove redundant template

2.3 (04/17/2023)
----------------
- Create apikey authentication for stock monitor
- Use constant-time compare for authentication
- Update docs and bump version

2.1 (04/10/2023)
----------------
- Replace string to `enum` for condition on linux OS
- Update release notes

2.0 (04/09/2023)
----------------
- Disable security mode trigger via offline on Linux
