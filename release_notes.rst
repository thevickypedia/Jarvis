Release Notes
=============

3.7.1 (09/11/2023)
------------------
- Includes a feature to upload any file to the server via Jarvis API or Telegram bot
- Unrecognized functions now have an offline option with stored GPT history
- Improved stability in speech recognition
- Fixes minor inconsistencies specific to volume controls on RokuTV
- Improves overall file structure

3.7 (08/29/2023)
----------------
- Includes a new feature to setup daily alerts for ``stock-monitor``
- Addtionally Jarvis can also list existing reminders now
- Improve overall stability and error handling for FileIO operations

3.6 (08/22/2023)
----------------
- Implement a feature to check for overlap in alarms
- Add a feature to get existing alarms
- Handle deletion of more than one alarms
- Remove env var for pre-commit
- Remove filtering process name for pre-commit
- Fix broken docs

3.5.1 (08/18/2023)
------------------
- Adds a new feature to request holidays on any date/day
- Minor improvements in stability

3.5 (08/10/2023)
----------------
- Adds a new feature to place functional restrictions on offline commands
- Bug fixes for TV and garage door controls
- Includes a retry logic for garage controls making it more reliable

3.4 (07/31/2023)
----------------
- Includes bug fixes and startup improvements
- Updates keyword mapping
- Updates to standalone test modules

3.3 (07/28/2023)
----------------
- Adds a feature to get all stock tickers via API
- Includes bug fixes and startup improvements

3.2 (07/22/2023)
----------------
- Adds a new feature to analyze stocks

3.1.3 (07/19/2023)
------------------
- Allow multiple tasks to run simultaneously in automation
- Allow high and low threshold for weather alerts

3.1.2 (07/12/2023)
------------------
- Includes bug fixes on response to failed to lights' response

3.1.1 (07/11/2023)
------------------
- Includes a new feature to allow ``secure-send`` via UI
- Implements a better approach to distinguish smart devices
- Minor performance and stability improvements

3.1 (07/01/2023)
----------------
- Includes bug fixes on vehicle connections
- Includes a new feature to set timed restarts via automation
- Improved logging for better visibility

3.0 (06/27/2023)
----------------
- Includes a new feature to have a custom keyword mapping
- Removes redundancy in weather alerts
- Now there is no manual intervention required to store LG tv's client key

3.0 (05/08/2023)
----------------
- Optimized memory usage and less redundant stuff

2.7 (05/05/2023)
----------------
- Adds a new feature to share local env vars and AWS secrets via secure endpoint
- Reduces break time on Telegram API by introducing retry logic
- Runs all cron jobs once during startup
- Includes support for different units for temperature and distance
- Improved logging
- Includes minor bug fixes on offline commands

2.7 (05/04/2023)
----------------
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

7.0.8 (01/29/2023)
------------------
- Make Jarvis pip installable
- Onboard to pypi with pyproject.toml
- Create an option to stop Jarvis via fastapi with an override flag
- Disable tunneling by default and enable with a flag
- Fix path for indicators and apple scripts
- Fix auto discover api routers for pypi package
- Remove git versioning and GitPython dependencies
- Switch python-publish.yml workflow to build on release and support pyproject.toml

6.9.4 (01/05/2023)
------------------
- Restructure Jarvis API
- Setup dedicated logger module for API
- Send OTP from stock-monitor endpoint to Jarvis via headers
- Break giant application into modules with routes
- Support updating keywords for Jarvis API
- Set stock_monitor.py to run on weekends
- Avoid reading keywords.yaml file when it's not modified
- Update README.md and docs

6.9.1 (01/04/2023)
------------------
- Make `stock-monitor` endpoint open-source
- Setup email verification service using one time passcodes
- Create custom email template for stock monitor OTP
- Set Jarvis API version to match main module

6.9.0 (01/02/2023)
------------------
- Add exception handlers in `stock-monitor` endpoint for JWT
- Fix native audio conversion in tts_stt.py
- Get plain text information for `stock-monitor` GET requests

6.8.9 (01/02/2023)
------------------
- Read background tasks via YAML file instead of env vars
- Change some HTTP requests methods from POST to GET calls
- Add an option to disable background tasks on demand
- Make `yaml` files in fileio directory to be available via API calls
- Update README.md

6.8.7 (12/31/2022)
------------------
- Add an api endpoint to get voices available for speech synthesis
- Make API docs page look neater

6.8.5 (12/31/2022)
------------------
- Add custom `processName` to log format
- Override logging filter to add process name
- Create process mapping file along with the components handled
- Use timed wait to optimize CPU utilization on long-running processes

6.8.3 (12/29/2022)
------------------
- Bug fix on `background_tasks`
- Move background tasks from thread to process as `called_by_offline` flag should not be set in main process
- Running it as a thread will raise `RuntimeError` as `runAndWait()` will not be called
- Remove unsafe code in `pluralize` function

6.8.0 (12/25/2022)
------------------
- Add feature to control multiple TVs simultaneously
- Iterate over a loop to power on and launch home for RokuTVs
- Improve type hints

6.7.9 (12/25/2022)
------------------
- Bug fix for `RokuTV`
- Check for existing app before launching `Home`
- Fix method fetching current app on TV

6.8.8 (12/24/2022)
------------------
- Add support for multiple TVs and add `RokuTV` controls
- Restructure the usage of `smart_devices.yaml` file
- Update README.md and requirements.txt

6.7.7 (12/23/2022)
------------------
- Load `PyAudio` during start up to avoid `ALSA` errors on `Linux`
- Add a condition check for weather location to avoid crash
- Remove the usage of `time.perf_counter()`
- Optimize globally accessible variables

6.7.6 (12/21/2022)
------------------
- Add an option to choose between microphones to use
- Implement a better way to get audio IO devices info

6.7.3 (12/17/2022)
------------------
- More optimizations for Linux
- Rename automation.yaml instead of removing if invalid
- Allow an option to brute force non-limited mode
- Fix release notes hyperlink in pypi
- Update README.md

6.7.2 (12/15/2022)
------------------
- Implement speech synthesis for linux systems
- Remove forcing limited mode for linux systems
- Fix a bug in surveillance mode session check
- Restrict alarm and reminder features in limited mode
- Add an option to set voice and quality for speech synthesis
- Delete docker container spun up for speech synthesis when stopped
- Block ALSA errors in Linux OS during start up
- Simplify models.py and update install.sh
- Initiate speech synthesis even in limited mode
- Include local changes when asked for Jarvis' version
- Add distributor info for linux systems

6.7.0 (12/11/2022)
------------------
- Add more `Linux` supporting features
- Write processes.yaml file regardless of limited mode state

6.6.8 (12/09/2022)
------------------
- Set smtp flag to false while email validation
- Update gmail-connector to the latest version

6.6.5 (11/29/2022)
------------------
- Add responses when garage door controller is offline
- Remove looping in garage module when device is chosen
- Send an email when vehicle is unlocked remotely
- Include timezone in vehicle's guardian mode response
- Create a dedicated module for functions that only uses builtins

6.6.4 (11/22/2022)
------------------
- Include usage of contacts.yaml file to send notifications
- Add a feature to send emails from Jarvis
- Avoid creating api/logs directory when running on limited mode
- Moves iOS related operations to a dedicated module
- Enable optional strict word match in word_match.py on top of regex
- Remove phrase being split on 'also' and make it a single command
- Fix a bug in windows brightness where increase and decrease were swapped
- Remove duplicate function arguments in listener.py
- Add potential future work

6.6.3 (11/19/2022)
------------------
- Fix a bug in garage door controller
- Identify the garage door by name
- Improve README.md
- Fix default password in vpn-server

5.5.0 (02/12/2022)
------------------
- Use microphone only when listeners are active
- Open and close audio streams gracefully
- Adjust to ambient noise in a dedicated thread
- Rename car connectors and controllers
- Add tv controls to offline communicator
- Take source app for meetings from env vars
- Set a global file to share dictionaries across modules
- Split speaker and microphone modules from main module
- Add progress of VPN Server creation vs deletion
- Move wake words to conversation.py
- Save smart devices IPs into smart_devices.yaml during quick restart
- Remove unnecessary OOP from conversation.py, keywords.py and database.py
- Update .gitignore and docs
- Restructure code

5.4.8 (02/10/2022)
------------------
- Change logging config to uvicorn style
- Remove unnecessary exception handlers
- Change location dumper to dict from list
- Remove unnecessary variables

5.4.9 (02/10/2022)
------------------
- Change logging config to uvicorn style
- Remove unnecessary exception handlers
- Change location dumper to dict from list
- Remove unnecessary variables

5.4.7 (02/08/2022)
------------------
- Restrict car unlock via offline communicator
- Remove super class and inter module connections for car
- Increase ping timeout for tv ip
- Restructure unrecognized dumper
- Set to restart Jarvis every 8 hours
- Fix tv_mac being unset during quick restart
- Change api logger to uvicorn to match the same format
- Remove line numbers from noqa

5.4.6 (02/06/2022)
------------------
- Make adaptable temperature values during car startup
- Increase iterations to turn on TV
- Modify docstrings on car controller

5.4.5 (02/03/2022)
------------------
- Simplify climate setting for car start
- Change logger location to current working directory
- Update CHANGELOG

5.4.3 (01/30/2022)
------------------
- Play a sound when connecting to car module
- Fix incorrect argument for remote engine start
- Remove default value on expiration time

5.4.2 (01/30/2022)
------------------
- Move independent functions out of main module
- Update README.md and docs

5.3.9 (01/29/2022)
------------------
- Update description of Jarvis API

5.4.1 (01/29/2022)
------------------
- Update description of Jarvis API

5.4.0 (01/29/2022)
------------------
- FEATURE::Jarvis can now control a Jaguar or LandRover
- Move env vars to module specific variables
- Update README.md and docs

5.3.8 (01/20/2022)
------------------
- Redirect API root to read-only page

5.3.7 (01/19/2022)
------------------
- Flush screen output before carriage return
- Upgrade sphinx version and update docs
- Update dotenv module version
- Update .gitignore

5.3.6 (01/10/2022)
------------------
- Use `vpn-server` from pypi package
- Bump common packages to >= versions
- Change variable name on offline_receive
- Use .touch to create pyicloud_error file

5.3.5 (12/11/2021)
------------------
- Make reminders to pick am/pm in any format
- Fix spell checks in docs strings

5.3.4 (12/11/2021)
------------------
- Avoid hitting os module for offline check
- Swap to dictionary instead
- Fix some offs in docs

5.3.3 (12/09/2021)
------------------
- Fix automation hour check
- Remove redundant keywords

5.3.2 (12/08/2021)
------------------
- Write automation data during JSONDecodeError

5.3.1 (12/07/2021)
------------------
- Fix some vague imports
- Update type hinting in docs strings

5.3.0 (12/05/2021)
------------------
- Fix module import without changing PYTHONPATH
- Change module imports to a recommended standard for API

5.2.9 (12/05/2021)
------------------
- Add docs section for Jarvis API

5.2.8 (12/04/2021)
------------------
- Use `:autoclass::` instead of `:automodule::` in index.rst
- Remove env var commit to ignore class members in docs
- Fix multiline docstrings
- Create new file for logging filters
- Re-arrange methods in fast.py

5.2.7 (11/30/2021)
------------------
- Simplify day and nighttime checks
- Fix item and category mismatch in database.py
- Revert customized imports

5.2.6 (11/22/2021)
------------------
- Add hyperlinks to watchlist stocks in report_gatherer.py
- Fix some wonky docstrings

5.2.5 (11/14/2021)
------------------
- Add a new model for robinhood authentication
- Use logging dict config for report gatherer
- Create logs dir if not found

5.2.4 (11/13/2021)
------------------
- Revert module level imports

5.2.3 (11/13/2021)
------------------
- Make watchlist feature in built
- Fix module level imports

5.2.2 (11/13/2021)
------------------
- Bugfix on `day` option for automations

5.2.1 (11/12/2021)
------------------
- FEATURE::Include `day` option for automations

5.1.9 (11/07/2021)
------------------
- Choose ports dynamically using socket module
- Update docs and ump version

5.1.8 (11/06/2021)
------------------
- Remove super class for alarms and reminders
- Add the alarm and reminder operation to automator
- Create directory for alarm and reminder on the go
- Log request and response from one place at conditions and speak

5.1.7 (11/05/2021)
------------------
- FEATURE::No special changes required for offline communicator
- text_spoken dict will handle the response when a text is spoken
- Remove speaker.runAndWait() and move it to say()

5.1.4 (11/02/2021)
------------------
- Move all speaker commands to a single function
- Include an exception handler for local API calls

5.1.3 (10/31/2021)
------------------
- Reduce one more long-running thread
- Add offline_communicator to automator
- Allow offline_communicator without changes to pyttsx3
- Allow robinhood to run without watchlists

5.1.2 (10/31/2021)
------------------
- Use `difflib.SequenceMatcher` to get the right device to locate
- Update README.md

5.1.1 (10/31/2021)
------------------
- FEATURE::Jarvis offline communicator has been made public and automations setup
- Make port number for offline communicator as an env var and default to a value
- Raise 500 if robinhood auth env var is not found but accessed
- Initiate robinhood related scripts on API startup only if the env var is present
- Block ngrok if JarvisHelper is not available but allow api trigger in localhost
- Setup on-demand automation.json to process some daily process and reduce background threads

5.1.0 (10/30/2021)
------------------
- Include conversation responses to offline compatible
- Split pre-checks for offline_communicator

5.0.9 (10/30/2021)
------------------
- Reduce number of long-running threads
- Check jarvis' status before writing offline_request file
- Fix SSID info retrieval breaking Jarvis

5.0.8 (10/29/2021)
------------------
- Default all args to `phrase`
- Prep to convert all conditions into a looped execution
- Move opencv from requirements.txt to installs.sh
- Handle multiple outputs coming from wolfram alpha
- Fix batch installation of dlib and cmake
- Make Jarvis work without env vars
- Default input_device_index to None in Activator
- Remove chatterbot as it is messy
- Some basic bug fixes
- Prep to convert all conditions into a looped execution

5.0.7 (10/25/2021)
------------------
- Fix issues with docstrings because of class variables
- Reduce number of unnecessary classes

5.0.6 (10/24/2021)
------------------
- Use comma separator for numbers in the 1000s
- Simply some code bits in robinhood.py

5.0.3 (10/23/2021)
------------------
- Change static methods to class variables in keywords.py and conversation.py
- Replicate changes to offline controller

5.0.1 (10/23/2021)
------------------
- Use `Jinja` to render html and enable dark-light mode toggle switch
- Store template in a python class instead of static.html
- Update requirements.txt
- Load CHANGELOG in reverse order of commit timeline

5.0.0 (10/23/2021)
------------------
- FEATURE::Jarvis API can now render investment portfolio as a static html
- Secure endpoint behind single-use token which is a hashed uuid
- Filter /investment?token=* logs as it will expose the single use token
- Instead have a custom warning logged
- Create static html file at given schedule including when app starts up
- Create logging config to match Uvicorn
- During doc creation remove docs dir after checking version.py
- Add robinhood_bg.jpg and static.html to support the static HTML file

4.9.9 (10/23/2021)
------------------
- Custom env vars are no longer needed for API as the .env can be shared

4.9.8 (10/22/2021)
------------------
- Restrict offline commands with `and` and `also` to process one at a time
- Handle pyicloud error gracefully during the initial start
- Create automator to perform custom automations at a given time
- Set initial timeout and phrase_limit in env vars and default to 3
- Remove plural for lights in keywords.py

4.9.7 (10/16/2021)
------------------
- Add timer to restart every 24h to get updated IPs and renew PID
- Modify Activator class to class objects from static
- Fix bug on directions

4.9.6 (10/15/2021)
------------------
- Onboard a shell script to build locally
- Add condition to abort if version.py wasn't modified
- Add changelog-generator to installs.sh
- Update requirements.txt, docstrings and CHANGELOG

4.9.5 (10/15/2021)
------------------
- Onboard to pypi
- Update README.md
