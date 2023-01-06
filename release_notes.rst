Release Notes
=============

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

6.9.3 (01/04/2023)
------------------
- Run multiple commands concurrently when sent via offline communicators
- This can't be implemented in main process as listeners and speakers can't overlap

6.9.2 (01/04/2023)
------------------
- Add a feature to mute for a certain amount of time
- Remove sprint name feature as source is broken and rare usage

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

6.8.8 (01/01/2023)
------------------
- `Bug fixes` and `Remove redundancies`
- Custom keyword mapping being overwritten
- Writing frequently used functions in yaml file
- Weather breaking when phrase is available but not place
- Remove redundant regex when getting capitalized

6.8.7 (12/31/2022)
------------------
- Add an api endpoint to get voices available for speech synthesis
- Make API docs page look neater

6.8.6 (12/31/2022)
------------------
- Set defaults on `SpeechSynthesisModal` as per env vars

6.8.5 (12/31/2022)
------------------
- Add custom `processName` to log format
- Override logging filter to add process name
- Create process mapping file along with the components handled
- Use timed wait to optimize CPU utilization on long-running processes

6.8.4 (12/31/2022)
------------------
- Remove overlapping `Thread` for background processes
- Run `wifi_connector` as a process to let `socket` sleep
- Add an option to set hours to ignore in background tasks
- Upgrade `PyAudio` for `macOS`
- More consistent logging
- Get CSS and JS required for night mode in robinhood.html via URL
- Ignore speaker.run when called by offline
- Update README.md

6.8.3 (12/29/2022)
------------------
- Bug fix on `background_tasks`
- Move background tasks from thread to process as `called_by_offline` flag should not be set in main process
- Running it as a thread will raise `RuntimeError` as `runAndWait()` will not be called
- Remove unsafe code in `pluralize` function

6.8.2 (12/29/2022)
------------------
- Make `time_converter` grammatically correct

6.8.1 (12/29/2022)
------------------
- Minor optimizations for memory usage and efficiency
- More clear logging and inline comments

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

6.7.8 (12/24/2022)
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

6.7.5 (12/20/2022)
------------------
- Remove `Javascript` from email_OTP.html

6.7.4 (12/20/2022)
------------------
- Load templates upon startup
- Add one click copy to emailOTP.html (Unsupported in emails)

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

6.7.1 (12/15/2022)
------------------
- Switch CHANGELOG to release_notes.rst
- Remove CHANGELOG from pypi and link it to github
- Add more classifiers for pypi

6.7.0 (12/11/2022)
------------------
- Add more `Linux` supporting features
- Write processes.yaml file regardless of limited mode state

6.6.9 (12/11/2022)
------------------
- FEATURE::Add `Linux` support
- Set to limited mode by default for Linux
- Update install.sh

6.6.8 (12/09/2022)
------------------
- Set smtp flag to false while email validation
- Update gmail-connector to the latest version

6.6.7 (12/07/2022)
------------------
- Change function names to avoid import conflicts

6.6.6 (12/06/2022)
------------------
- Save process IDs and name map in a yaml file
- Change module names to make better sense

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

6.6.2 (11/19/2022)
------------------
- Update issue templates

6.6.1 (11/19/2022)
------------------
- Add feature to autoconnect WLAN
- Onboard connector.py and connection.py modules
- Run a process in background to check internet connection
- Setup retry logic for internet check
- Add a template for xml config
- Add a function to get voice by gender in speak.py
- Log more information in subprocess errors
- Update install.sh, README.md and docstrings

6.6.0 (11/16/2022)
------------------
- Upgrade VPN server to include hosted zone access
- Update pypi publish to run only on release tags

6.5.9 (11/12/2022)
------------------
- Add multiple modules to test peripherals before startup
- Fix guardian mode and frame response with end time
- Include a public help message in Telegram API
- Enable an option to lock and then start the vehicle
- Condense connection errors into a single tuple for reuse
- Set text as name for error images generated
- Jarvis can now speak its version number
- Set file removal thread to daemon in fast.py
- Store keywords as a yaml file for optional custom keywords
- Keep rewriting keywords in background processes
- Update values in recognizer.py

6.5.8 (11/04/2022)
------------------
- Update README.md about bug in a dependent module
- Add optional voice name and voice rate as env vars
- Add a feature to adjust volume specific for Jarvis

6.5.7 (11/01/2022)
------------------
- Introduce custom recognizer settings
- Add test_listener.py for on-demand tests
- Remove all hard coded references
- Fix extract numbers function for integers
- Include investment endpoint in schema
- Fix log file appending * for subprocesses
- Include traceback for broad exceptions
- Update docstrings and README.md

6.5.6 (10/31/2022)
------------------
- Switch single use tokens to multifactor authentication via email
- Add optional DEBUG option for logs
- Create new email templates for one time passcodes
- Timeout one time passcodes after 5 minutes in a thread

6.5.5 (10/30/2022)
------------------
- Add feature in stock monitor to generate price graph
- Remove alert data after sending out one price alert
- Include multiple attachments in a single alert
- Remove f-strings in database queries
- Move email_validator.py to gmail-connector module

6.5.4 (10/28/2022)
------------------
- Improvements to `stock-monitor` endpoint
- Give an option for users to include data GET/DELETE existing alerts
- Filter outbound data from database by the email input received
- Rename monitor.html to surveillance.html in templates module

6.5.3 (10/27/2022)
------------------
- Create an open-source stock price monitor within Jarvis
- Create a database for stock monitor to store the user information
- Extract all NASDAQ tickers to validate user input
- Prevent users from adding duplicate entries
- Onboard stock_monitor.py to monitor stock price and trigger notifications to users
- Onboard email_validator.py
- Onboard applauncher.scpt to check if app is closed before opening
- Use special character in f-string to add quotes within a string
- Remove screen print for camera validation
- Upgrade gmail-connector
- Setup manual workflow dispatch for pypi build

6.5.2 (10/20/2022)
------------------
- Improvements to surveillance
- Generate an on demand image frame using text
- Communicate to the UI if webcam has failed
- Let server handle the session timeout
- Remove session timeout from the UI
- Wrap offline tasks into bare exception to communicate the error
- Change surveillance endpoint to be condition based
- Update requirements.txt and README.md

6.5.1 (10/16/2022)
------------------
- Fix rendering same webcam feed for different sessions
- Get streaming URL from window.href in HTML automatically
- Take surveillance mode session timeout as env vars
- Set number of API server workers as env vars
- Insert gen_frames process ID into children table upon start
- Remove timeout for report gatherer html page
- Configure dedicated log formatters for multiprocess loggers
- Open images when a picture is taken by Jarvis

6.5.0 (10/15/2022)
------------------
- Add surveillance endpoint using live feed from cameras
- Implement websockets to identify client disconnect
- Use process sharing queue to put and get frames
- Stream live webcam by getting camera index ID
- Add a 5-minute timeout for robinhood endpoint
- Update .gitignore
- Use secrets.compare_digest to validate auth
- Remove display feature after capturing an image

6.4.9 (10/09/2022)
------------------
- Add feature to capture image from connected camera
- Onboard a module to list camera names
- Support USB cameras for video and photo operations
- Support flushing screen for command-line executions
- Add photo capture feature to offline-communicator
- Restructure facial recognition and detection process
- Enable an option to display the live feed in face detection
- Restructure guardian mode
- Remove notification during initialization
- Remove notification for broad exception in Jarvis main module
- Add start up checks for camera feed and indices
- Move all HTML templates to its own module

6.4.8 (09/30/2022)
------------------
- Multiprocess logs go to dedicated log files
- Clean up unused log configurations
- Move logger.py into modules

6.4.7 (09/28/2022)
------------------
- Add a feature to toggle flashing disco lights
- Create a custom auth bearer for future use
- Simplify lights function in lights.py and add lights_squire.py
- Simplify creating database tables and columns
- Remove CORS for ngrok as tunneling doesn't trigger redirects
- Rename garage.py to myq_controller.py
- Move repeated tasks to a dedicated function
- Change log level to debug for entries that are sparingly required
- Update docstrings, README.md and docs

6.4.6 (09/21/2022)
------------------
- Add screen lock feature on `WindowsOS`
- Add speech synthesis feature via offline-communicator

6.4.5 (09/15/2022)
------------------
- Add a feature to set repeated alarms
- Create a module to trigger notifications in WindowsOS
- Support notifications in Windows OS
- Add exception handlers for all egress calls

6.4.4 (09/14/2022)
------------------
- Raise `LookupError` if ngrok URL is not found
- Add broad exception clause for the main module
- Secure keywords and conversations endpoints in API
- Improve type hinting

6.4.3 (09/13/2022)
------------------
- Remove google search parser and its dependencies
- Get ngrok url via offline communicator

6.4.2 (09/03/2022)
------------------
- Fix task execution using `after` sent via `TelegramAPI`
- Default wake words for legacy macOS to working modules

6.4.1 (09/03/2022)
------------------
- Improve wait time after wake word detection
- Minor improvements to reduce line numbers
- Remove un-used lines of code

6.4.0 (08/31/2022)
------------------
- Add individual sensitivity values for wake words
- Run asynchronous functions using threads when called by API
- Create custom class for validating sensitivity
- Update README.md and setup.py

6.3.9 (08/28/2022)
------------------
- Fix missing location file in `LIMITED` mode
- Avoid location coordinates being 0.0
- Remove redundancy in loop stopping child processes
- Remove bluetooth feature as it is unreliable and slow

6.3.8 (08/26/2022)
------------------
- Add wake-word detection feature for macOS older than 10.14
- Build docker client within exception handler
- Update requirements.txt and install.sh

6.3.7 (08/24/2022)
------------------
- Run speech synthesis via `docker-py`
- Fix logging issue in windows
- Fix broken multiple execution in Telegram API
- Better log child process termination
- Add missing speaker entry for garage actions

6.3.6 (08/19/2022)
------------------
- Bug fix: Move logger disable to function level
- Bug fix: Don't log in word_mach when called by automation

6.3.5 (08/19/2022)
------------------
- Integrate `MyQ` garage open and close feature

6.3.4 (08/18/2022)
------------------
- Add `LIMITED` run feature for machines with lower performance
- Avoid using the method "any" for performance and logging ability
- Remove redundancy in variable re-declarations
- Remove uncovered exception in lights.py for offline communicator
- Update README.md
- Minor bug fixes

6.3.3 (08/13/2022)
------------------
- Fix memory leak due to audio frames storage
- Add display controls for Windows OS
- Remove external dependencies for volume controls on Windows OS
- Fix OS specific bugs in report_gatherer.py
- Create a new pydantic class for Settings
- Remove redundant variables

6.3.2 (08/08/2022)
------------------
- Handle broad exception clause during offline execution
- Renew only thrice
- Fix message feature without a phone number
- Fix ip address vs internet checker
- Fix ngrok tunneling check
- Fix failed tv request from turning on the tv
- Fix extra spacing issues

6.3.1 (08/02/2022)
------------------
- Support timezones with robinhood report generation
- Modify extended market hours in rh_helper.py
- Configure response for phrases with abusive words
- Remove delete db during stop process and replace with clear db
- Replace INSERT statements with INSERT or REPLACE
- Clear tables before inserting new values
- Modify existing ngrok tunnel check

6.3.0 (07/29/2022)
------------------
- Move default cron expression to rh_helper.py
- Fix docs alias

6.2.9 (07/28/2022)
------------------
- Configure more than one wake word for Jarvis
- Create custom validation classes for models
- Update README.md

6.2.8 (07/27/2022)
------------------
- Support crontab expressions from env vars
- Remove external dependency for crontab
- Create a new module for tasks execution at set intervals
- Stop all child processes including crontab
- Start and stop background tasks in the main module

6.2.7 (07/26/2022)
------------------
- Add an option to set up scheduled tasks
- Run starter function upon restart
- Support remind now
- Remove restart.py
- Update README.md

6.2.6 (07/22/2022)
------------------
- Remove JLR api call for reverse geocoding and use default
- Delete DB only when main module is stopped
- Fix restart module args

6.2.5 (07/22/2022)
------------------
- Log difference between old and new data in automation
- Avoid baseConfig and replace it with logging handler
- Delete DB only when terminating main module
- Fix restart main module vs child processes
- Write into new log file after restart

6.2.4 (07/19/2022)
------------------
- Remove self restart functionality
- Restart sub processes via offline communicator
- Fix failed connections bug in telegram.py

6.2.3 (07/19/2022)
------------------
- Handle broken reverse-geocode call in `JLR API`
- Replace HTTP status codes with built-in
- Remove redundancy on restart module
- Remove offline restart feature for future improvement
- Add local commit check on CHANGELOG update

6.2.2 (07/06/2022)
------------------
- Fix bug on start up for wired internet connections
- Remove case-sensitive check on Telegram greetings
- Check real path in report_gatherer.py
- Update install.sh to include git for windows

6.2.1 (07/03/2022)
------------------
- Check offline compatible request during each iteration
- Implement a timed delay between iterations
- Remove grouping non-built-in exceptions
- Remove logging speaker called by in main log during offline comm

6.2.0 (06/26/2022)
------------------
- Add ability to perform scheduled restart with `automation.yaml`
- Group all network errors into one class
- Delete entries from DB when restarted or stopped
- Log messages in retry module only if func failed in 1st attempt
- Fix spacing bug in reminder executor
- Set auth to empty string for offline communicator
- Set retry module to raise warning instead or exception

6.1.9 (06/21/2022)
------------------
- Have an option to process audio in native voice
- Move all text to speech and speech to text into a single module
- Fix text to audio conversion
- Remove pyaudio wheel file once installed

6.1.8 (06/20/2022)
------------------
- Add a `retry handler` for database functions during multiprocessing
- Check python version in install.sh
- Check lock status before trying to remote start the car
- Set timeout for database connection
- Bug fixes on speaker.py and weather.py

6.1.7 (06/16/2022)
------------------
- Stop `subprocess` created by child processes when stopped
- Remove redundancy when making requests in bot.py
- Move all table creation to modules.py
- Add exception handler for invalid ticker symbol in report_gatherer.py
- Move vpn state check to database instead of shared variable
- Create a test database class in database.py

6.1.6 (06/14/2022)
------------------
- Add host for speech synthesis as an optional env var
- Fix speech synthesis assuming timestamp to be in 24-hour format
- Add different response messages for alarms and timers
- Add an option to get only sun rise and sunset timings
- Fix return values for a few api calls

6.1.5 (06/13/2022)
------------------
- Remove status call on speech synthesis
- Add xcode in install.sh
- Add safety check on port numbers
- Add multiple responses for greetings
- Add host as an arg for tunneling
- Stop logging speaker text in two places
- Fix port number arg in docker command

6.1.4 (06/12/2022)
------------------
- Close `audio_stream` before opening `Microphone`
- Support `Jarvis_API` even further
- Replace ° sign with unicode string
- Add api paths for keywords.py, conversation.py and offline_compatible
- Fix speech_synthesis module
- Narrow conditions for speedtest
- Remove special characters in conversation.py and keywords.py
- Remove unused shared resources

6.1.3 (06/10/2022)
------------------
- Add more options to run via offline communicator
- Fix send_sms in communicator.py
- Allow and, also and after conditions in offline communicators
- Append recorded frames by default

6.1.2 (06/08/2022)
------------------
- Translate hostname to IPv4 address and extend interface
- Get assigned IP of smart devices when host uses multiple interfaces
- Base tv status off IP instead of shared resources
- Remove car unlock - offline restriction
- Reorder conditions.py
- Include zero in extract numbers function
- Add current date to meetings and events db to filter outdated information

6.1.1 (06/06/2022)
------------------
- Use `Microphone` as a shared value across all modules
- Avoid reopening audio stream for every iteration
- Log timeout events optionally
- Check response for car tasks
- Default delay timeout type to second
- Reduce duration for acknowledgement.mp3

6.1.0 (06/05/2022)
------------------
- Remove exit message when stopped via `TelegramAPI`
- Remove continue statements to include future lines
- Move listener related exception handlers to listener.py
- Move db checks from main module to support.py

6.0.9 (06/04/2022)
------------------
- Check network id of host machine against smart devices
- Remove hard coded check for network id
- Move save recording timeout arg to env vars
- Remove print statements for listener

6.0.8 (06/03/2022)
------------------
- Add optional multi `macaddress` for the same television
- Create threadpool to turn on a tv
- Reduce ping timeout to check tv status
- Install PyAudio for Windows using wheel file
- Record audio frames and store it for analysis
- Sort unrecognized dictionary as LIFO
- Fix file paths by using joins
- Add default volume as an env var
- Remove usage of 'SR_ERROR' as string
- Remove concurrent process response for offline communications
- Remove unused functions
- Update README.md, install.sh and requirements.txt

6.0.7 (05/30/2022)
------------------
- Add an option to terminate Jarvis via `TelegramAPI`
- Move voice message handler to a dedicated module
- Add optional timeout for voice message handling
- Handle connection errors differently

6.0.6 (05/26/2022)
------------------
- Add exception handlers for loading `yaml` files
- Delete pycache from all sub-dir during startup
- Update README.md

6.0.5 (05/25/2022)
------------------
- Add a generic `function-timeout` module
- Use sockets to get IP of hostname instead of using Netgear module
- Update tv.py and lights.py to match using sockets to find IP address
- Have an option to retain location.yaml file for accurate location information
- Add exception handlers for loading yaml files
- Remove the usage of hostnames.yaml
- Detect lights that are not connected to the internet

6.0.4 (05/21/2022)
------------------
- Support voice commands via `TelegramAPI` on Windows
- Create a timeout handler for windows
- Use `ffmpeg` to convert `ogg` to `wav` on WindowsOS
- Add default value for ip_scanner.py to avoid errors during internet disconnection
- Add exception handler for windows specific process error

6.0.3 (05/17/2022)
------------------
- FEATURE::Jarvis can process voice commands via `TelegramAPI`
- Convert ogg to flac to mp3 to handle voice command requests
- Fix hostname being wonky using strip
- Add new shared variable to identify caller function name
- Fix shared hosted_device information missing in multiprocessing
- Print voice module information optionally
- Onboard timeout handler for a particular function or a task
- City and hamlet are equivalent in location

6.0.2 (05/15/2022)
------------------
- Set car temperature based on the vehicle's location
- Get closest match for lights controls
- Reduce redundancy in location.py
- Add more logging for missing fileio
- Add more exception handlers for URL requests
- Add a class for indicators to load all mp3 files upon startup

6.0.1 (05/11/2022)
------------------
- Set incoming message process timeout for `TelegramAPI`
- Fix car temperature mixed up with weather
- Speak out meetings in the past as well
- Avoid stopping Jarvis due to connection issue
- Block process until acknowledgement tone is played for legacy
- Sort robinhood report by top gainer and top looser
- Move robinhood.html from api/ to fileio/
- Add more exception handlers to tv_controls.py

6.0.0 (04/29/2022)
------------------
- Allow `Float` and `Int` for sensitivity, timeout and phrase limit
- Avoid playing tv scan message when called by offline
- Remove redundant functions
- Change exceptions name
- Fix install.sh

5.9.9 (04/22/2022)
------------------
- Fix target temperature for vehicle's remote start
- Fix reminder message having _ in it
- Create a new custom exception for TV
- Check ics_url status code before running schedule
- Have an optional port number for speech synthesis
- Fix TV errors when unable to find or scan
- Add more keywords

5.9.8 (04/15/2022)
------------------
- Get smart-lights location name from `hostnames.yaml`
- Speak a message if unable to connect to particular lights
- Remove unnecessary OOP from jarvis.py
- Handle / commands to support shortcuts
- Add more introductory words to welcome message in Telegram API
- Add more support functions to support.py
- Fix redundant event wishes during night message
- Re-arrange conditions.py as per frequently used
- Add ISSUE_TEMPLATE and update README.md

5.9.7 (04/10/2022)
------------------
- Enable `speech-synthesis` for offline-communicator
- Remove redundant checks for timeout env var
- Update README.md

5.9.6 (04/10/2022)
------------------
- Process requests to `speech-synthesis` instead of redirect
- Simplify docker container check before using default audio

5.9.5 (04/10/2022)
------------------
- Onboard optional speech synthesis running on docker
- Start larynx process as part of other background processes
- Set up an endpoint using fastapi to access the docker page
- Fix imports and os specific file paths

5.9.4 (04/08/2022)
------------------
- Use context manager for database connections
- globals.py -> shared.py
- Wrap main initiators within a single class
- Remove wakeonlan package and add it to wakeonlan.py
- Remove await method for database commits
- Add *.txt files to .gitignore

5.9.3 (04/08/2022)
------------------
- Fix DB error when running `INSERT` queries parallely
- Fix old response when no response from Jarvis for offline comm
- Fix key error on training data when multiple entries get written at the exact same second
- Move apple script files into fileio directory
- Change some global flags from dict to bool variables

5.9.2 (04/06/2022)
------------------
- Fix `null` response during offline communication
- Fix list to string when logging offline response
- Group OS independent modules in install.sh
- Fix Windows OS start up bugs

5.9.1 (04/05/2022)
------------------
- Avoid using database for offline communication
- Split create_table in database.py
- Write events and meetings into base database
- vpn_checker function to only return IP when VPN is not connected
- Differentiate stop and pause in tv.py
- Update requirements.txt

5.9.0 (04/03/2022)
------------------
- FEATURE::`honk/blink` and `locate` a car
- Do not ring device when asked to locate from offline
- Launch events app only during startup

5.8.9 (04/03/2022)
------------------
- Fix `OperationalError` upon inserting data into DB
- Avoid stopping speaker module when called by offline
- Log warning if router pass is present but not hostnames.yaml
- Have an optional env var for meetings and netgear's sync intervals

5.8.8 (03/31/2022)
------------------
- Ignore meetings occurred same day in the past
- Go easy on getting city and state info from fileio/location.yaml
- Create dedicated database for events and meetings
- Remove the global dict warm_light
- Get location information from IP address instead of speedtest module
- Default event_app to calendar
- Have a strict mode in report_gatherer.py to ignore purchased stocks in watchlist

5.8.7 (03/27/2022)
------------------
- Default to location by IP address during startup
- Update README.md on startup instructions and remove WIP banner

5.8.6 (03/27/2022)
------------------
- Remove market status condition to gather `robinhood` report
- Fix google home device scanner
- Move offline_compatible words into its own module
- Move hashed token into support.py
- Remove appscript and use osascript instead for tunneling
- Move legacy phrase limit to env var

5.8.5 (03/26/2022)
------------------
- Fix open connections on database and iPhone locator
- Differentiate all day events in meetings

5.8.4 (03/26/2022)
------------------
- Fix background process initiating incorrect method
- Use base db to write meetings/events information
- Change time format while reading meetings
- Add logs when scanning for meetings/events

5.8.3 (03/26/2022)
------------------
- FEATURE::Jarvis can read meetings from ICS URLs
- Use single install script and requirements.txt
- Increase phrase limit in legacy mode to 3 secs
- Onboard a new module to read .ics urls
- Move LOCAL_TIMEZONE to globals.py
- Update README.md and requirements.txt

5.8.2 (03/24/2022)
------------------
- FEATURE::Jarvis can tell random sprint names
- Create custom exceptions with meaningful names
- Run speaker for each iteration during and or also
- Fix typos in doc strings and README.md

5.8.1 (03/21/2022)
------------------
- Fix existing features on Windows OS
- Add an unsupported message for non-existing ones
- Add legacy keywords as an optional env var

5.8.0 (03/20/2022)
------------------
- FEATURE::Jarvis supports Windows OS once again

5.7.9 (03/19/2022)
------------------
- Use device hostnames from a source yaml file
- Bump uvicorn version and clean up requirements.txt
- Move stopper functions from support.py to controls.py
- Show a warning message during installation for legacy versions
- Re-arrange conditions.py as per frequently used
- Simplify .gitignore

5.7.8 (03/16/2022)
------------------
- Fix local IP address reading `localhost`
- Remove .lock file from fileio
- Remove fileio and logs when building docs

5.7.7 (03/15/2022)
------------------
- FEATURE::Jarvis supports older MacOS versions
- Fix bug in getting icloud default device
- Stop notification for missing folder in calendar
- Get system information in a more eloquent way
- Check for Telegram Bot api key before start up
- Split start and stop background processes into a dedicated module
- Simply fetching local IP address
- Add logging in listener.py
- Change kwargs to be more meaningful

5.7.6 (03/14/2022)
------------------
- Create a `pydantic` model to load all `FileIO` paths
- Store all file operations in fileio directory
- Add road name to string of address when asked
- Fix meetings file re-written all the time
- Write frequent files in max called first order

5.7.5 (03/13/2022)
------------------
- Stop listeners and remove db file while restarting
- Create a dedicated db file for tasks
- Handle exceptions in telegram bot more valiantly

5.7.4 (03/13/2022)
------------------
- Alarm/reminder execute after certain minutes/hours
- Create a new function to extract time from a string
- Verify session for telegram connection
- Add a deprecation message for slash commands in telegram
- Drop offline and restart tables when restarting
- Set a method validation for extract_nos function
- Remove keyword args from conditions.py
- Do not remove punctuations when a command is sent via offline
- Rename db as offline db (odb), restart db (rdb) and tasks db (tdb)
- Single quotes to double quotes in keywords.py
- Move static methods and fix imports outside class in smart_lights.py
- Set optional arg to extract_nos as int or float

5.7.3 (03/12/2022)
------------------
- Add a new custom module for `TelegramAPI`
- Do not regenerate location.yaml if timestamp is missing
- Fix .env path
- Add should return flag for offline executions
- Suppress coin flip sound when triggered by offline

5.7.2 (03/11/2022)
------------------
- Predict gender of a user in ``TelegramAPI`` responses
- Remove hard coded title as `sir` and set as env var
- Remove hard coded name as Vignesh and set as env var
- Speak alarm deletion confirmation instead of printing on the screen

5.7.1 (03/11/2022)
------------------
- Create a `restart` flag in `database` to kill processes
- Control all restarts from restart_control
- Avoid duplicate processes when restarted

5.7.0 (03/11/2022)
------------------
- FEATURE::Jarvis uses `TelegramAPI` for offline comm
- Do not check same threads for database connections
- Do not write into offline table when there is an existing request
- Gather all logging configuration in one module
- Gracefully terminate all background processes before restart
- Do not execute commands with 'after' via online communicator
- Remove multiple restart and disable restart via offline statements
- Gather all articles into a statement for news

5.6.9 (03/06/2022)
------------------
- Stop loading env vars when `Investment` runs as cron
- Remove unused stopper function
- Remove generated time for location reload
- Update hyperlinks on README.md

5.6.8 (03/05/2022)
------------------
- Use base database for todo list
- Remove keywords for create and delete todo list
- Remove todo list module
- Fix issues with inserting records in the database

5.6.7 (03/05/2022)
------------------
- Create a `database` for offline interaction
- Remove unexpected arg from car.py
- Offline communication to use database instead of files
- Remove secondary class to load env vars
- Load robinhood env vars during class instantiation

5.6.6 (03/03/2022)
------------------
- Add `update` keyword to avoidable
- Convert str to int directly instead of including float in the loop

5.6.5 (03/01/2022)
------------------
- Add an option to update `Jarvis` without manual interrupt
- Set timeout to wait on terminate process and kill it
- Reload env vars upon restart
- Use github module instead of cli tool to perform git pull
- Use default logging for car connector

5.6.4 (02/28/2022)
------------------
- Introduce `timestamp` in `location.yaml` to reuse upon restart
- Validate timestamp in location.yaml to re-write or re-use
- Create a new function for frequently called methods to re-arrange conditions block

5.6.3 (02/27/2022)
------------------
- Move all spoken phrase handlers to commander.py
- Offline commands go directly to conditions
- Avoid 0 metrics in time_converter

5.6.2 (02/27/2022)
------------------
- Change API `Authorization` from data to `Header`
- Create a module to authenticate headers
- Change response code for expired tokens
- Do not delete lock files of alarms and reminders

5.6.1 (02/26/2022)
------------------
- Split conditions out of main module
- Create a dedicated module for splitter
- Add missing requirement in requirements.txt

5.6.0 (02/26/2022)
------------------
- Load env vars using `pydantic` to validate during startup
- Pre-check VPN Server config file before initiating process
- Log background process name and PID
- Catch car connection error
- Move database.py to tasks.py
- Change arg name in offline communicator
- Set robinhood_token dict to an empty string
- Remove unnecessary path appends

5.5.9 (02/25/2022)
------------------
- Use YAML instead of JSON file for automation setup
- Remove status flag from automation file and set when needed
- Update clear_logs to scan files within the logs/api dir
- Gracefully terminate background processes when shutdown
- Remove default args from automation function
- Bump fastapi version and add Pillow to requirements.txt
- Exclude env vars from docs

5.5.8 (02/24/2022)
------------------
- Use ``Process`` instead of ``Thread`` for long-running tasks
- Use the right way to get timezone in API response
- Include dry_run option in automator to start certain tasks
- Write ** in log file only when triggered from main process
- Kill background processes in a more graceful way
- Disable access log from going to default logs
- Remove quick restart feature
- Remove checking jarvis status function in API
- Remove unnecessary default arg for automation that's never changed
- Remove storing location dict in memory and use it from yaml file instead
- Remove bash commands and use os module instead to create file and directories

5.5.7 (02/23/2022)
------------------
- Remove `personalcloud` feature for good
- Remove threading for offline communicator from automator
- Make local build script more generic
- Add root user to globals.py
- Update and test versions of all third-party modules
- Setup a new module to get free ports and kill an existing port
- Update CHANGELOG and docs

5.5.6 (02/19/2022)
------------------
- Use read email feature from `gmailconnector` module
- Split modules into more executors
- Remove usage of pydictionary module due to breakage
- Remove .has_been_called and add it to globals as a dict
- Rename certain modules
- Disable docs workflow

5.5.5 (02/17/2022)
------------------
- Split modules into more executors
- Update docs

5.5.4 (02/16/2022)
------------------
- Create an `APIServer` to override `uvicorn.Server`
- Handle install signal handlers to run uvicorn server in a thread
- Kill PID listening on offline port if un-reachable
- Set up an option to enable and disable the automation execution
- Add automation controller to offline communication compatible
- Reload logging module since there are multiple loggers
- Split off tasks with display to its own executors
- Remove endpoint filters for logging in API
- Load all env vars in a class within globals.py
- Add a pytest file for basic server config
- Update requirements.txt, README.md, .gitignore, and docs

5.5.3 (02/13/2022)
------------------
- Remove ambient noise suppression
- Remove OOP from personal cloud
- Implement executors individually
- More module re-factorization
- Load current location into a global dict

5.5.2 (02/12/2022)
------------------
- Add a screen flush function to support.py
- Remove webpage open feature
- Upload to pypi on commit to master branch

5.5.1 (02/12/2022)
------------------
- Look for existing apps and sources in TV before launch
- Resolve inconsistencies in google function and tv_controls.py
- Update docs

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

5.4.9 (02/10/2022)
------------------
- Change logging config to uvicorn style
- Remove unnecessary exception handlers
- Change location dumper to dict from list
- Remove unnecessary variables

5.4.8 (02/09/2022)
------------------
- Create investment endpoints based on env vars
- Remove custom log config
- Increase usage of dumping unrecognized words into yaml file
- Make the training file much more explanatory
- Increase usage of get_capitalized method

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

5.4.4 (02/03/2022)
------------------
- Refactor modules to dedicated directories

5.4.3 (01/30/2022)
------------------
- Play a sound when connecting to car module
- Fix incorrect argument for remote engine start
- Remove default value on expiration time

5.4.2 (01/30/2022)
------------------
- Move independent functions out of main module
- Update README.md and docs

5.4.1 (01/29/2022)
------------------
- Update description of Jarvis API

5.4.0 (01/29/2022)
------------------
- FEATURE::Jarvis can now control a Jaguar or LandRover
- Move env vars to module specific variables
- Update README.md and docs

5.3.9 (01/27/2022)
------------------
- Split notifications and personal cloud to its own modules
- Handle empty list on watchlist
- Update README.md

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

5.2.0 (11/11/2021)
------------------
- Update responses from `gmail-connector`

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

5.1.6 (11/05/2021)
------------------
- Bug Fix: Don't read and write offline file in a single thread
- Bug Fix: Don't lock screens and lower volume during daytime
- Bug Fix: Remove punctuations in offline commands
- Avoid API calls for internal requests

5.1.5 (11/04/2021)
------------------
- Fix conflicts between automation and offline communicator
- Reference voice modules with model name instead of ID

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

5.0.5 (10/24/2021)
------------------
- Join hanging threads when API restarts/shutdown

5.0.4 (10/24/2021)
------------------
- FEATURE::Add cron schedule instead of dedicated Thread
- Add MarketHours dictionary to auto-schedule cron entries
- Add FileHandler for robinhood logs when triggered from main module
- Remove robinhood_bg.jpg and add favicon.ico instead

5.0.3 (10/23/2021)
------------------
- Change static methods to class variables in keywords.py and conversation.py
- Replicate changes to offline controller

5.0.2 (10/23/2021)
------------------
- Change static methods to class variables in keywords.py and conversation.py

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

4.9.4 (10/14/2021)
------------------
- auto upload to pypi when tagged a release version

4.9.3 (10/14/2021)
------------------
- Make `tv` variable as global to handle controls after shutdown

4.9.2 (10/10/2021)
------------------
- Extend `should_return` flag usage to avoid Jarivs picking up background voices
- Pass keyword arguments instead of unnamed ones
- Make timeout and phrase_limit mandatory
- Fix bug on Database deleter

4.9.1 (10/09/2021)
------------------
- Fix thread conflict when restarting from offline
- Avoid re-initialization on database class

4.9.0 (10/08/2021)
------------------
- Convert timezone after writing to yaml

4.8.9 (10/08/2021)
------------------
- Create a dedicated thread to trigger multithreading for lights
- Remove sensitivity from being passed as arg
- Add wait time when offline request and response files are found
- Include datetime in test message from offline communicator
- Include timezone in location.yaml

4.8.8 (10/07/2021)
------------------
- simplify installation process

4.8.7 (10/07/2021)
------------------
- Take sensitivity as an argument or env var or default: 0.5
- Return delete item with category from database.py
- strip away empty spaces and new lines while reading emails

4.8.6 (10/07/2021)
------------------
- Return when incorrect wake up by deep neural networks
- Add docstrings for should_return flag
- Rename wake up engine variable

4.8.5 (10/06/2021)
------------------
- Launch Calendar or Outlook upon startup to read meetings

4.8.4 (10/06/2021)
------------------
- Don't fail on missing music files
- Don't fail on current time when places aren't valid
- Change logger level for porcupine closure

4.8.3 (10/04/2021)
------------------
- Use porcupine module to detect hotword and startup
- Remove `sentry_mode` and update all references
- Add a startup tone for indication (similar to google home)
- Change some variable names

4.8.2 (10/04/2021)
------------------
- Create `logs` dir on demand
- Refactor installs.sh

4.8.1 (10/04/2021)
------------------
- Create `logs` dir on demand
- Refactor installs.sh
- Fix a bug with greet_check

4.8.0 (09/23/2021)
------------------
- Simplify `vpn_server` and add `quiet` flag to git command
- Remove apple script to perform vpn server operations

4.7.9 (09/23/2021)
------------------
- Add an env var `ENV: Jarvis` so, `vpn-server` can log the details in a log file
- Pull latest from git for vpn-server

4.7.8 (09/22/2021)
------------------
- Add exception handler and retry logic for vpn-server
- Get tv_mac while IPScan and remove arp command

4.7.7 (09/21/2021)
------------------
- Check for current instance of vpn before triggering a new one

4.7.6 (09/20/2021)
------------------
- FEATURE::Hook up `Jarvis` with `vpn-server` and `offline_communicator`
- Update keywords.py, README.md and other docstrings

4.7.5 (09/13/2021)
------------------
- Modify the way `activator` initiates, once invoked

4.7.4 (09/13/2021)
------------------
- TRIAL::Replace `critical` level to `info` level logging

4.7.3 (09/13/2021)
------------------
- Use `os.path.exists` instead of `os.listdir`
- Perform quick restart on demand
- Don't run certain threads if pre-req is unavailable to avoid exception handler
- Fix SNS to SMS
- Play an acknowledgement beep when activator is invoked

4.7.2 (09/12/2021)
------------------
- FEATURE::Jarvis can now perform quick restart in case of an error
- Load temporary env vars when restarted because of errors
- Create a _static folder if not available during pre-commit
- Remove completed todos
- Handle CommandErrors
- Upgrade sphinx version
- Update docstrings
- Add a todo

4.7.1 (08/30/2021)
------------------
- Fix bug on telling meetings when not needed
- Fix bug on warm_lights
- Fix bug when restart offered as offline command
- Create thread for deleting offline_request file
- Rename methods and remove a print statement
- Update docs and .gitignore

4.7.0 (08/29/2021)
------------------
- Add docstrings from `__init__` methods
- Don't wait for response from Jarvis when restarted offline

4.6.9 (08/29/2021)
------------------
- FEATURE::Jarvis API will now have conditions to allow non-interactive keywords via API calls
- Remove all global variables and use dict instead
- Split controller away from API as a dedicated module
- Set and unset env var for called_by_offline so functions can avoid speaker.runAndWait

4.6.8 (08/28/2021)
------------------
- FEATURE::Jarvis API can now send the response of offline commands
- Write response for offline_comm in a file
- Fix origin regex for ngrok
- Do not send offline response via SMS

4.6.7 (08/28/2021)
------------------
- Perform offline request despite `RuntimeError`
- Change log format from 24h to 12h
- Add timezone conversion for test logging
- Add a feature to restart quietly in case of `RuntimeError`
- Update docstrings

4.6.6 (08/25/2021)
------------------
- Remove empty line at start of `logFile`

4.6.5 (08/25/2021)
------------------
- Avoid listing directory to check file presence
- Change log file only once per day
- Add wildcards during start of log file
- Set an env var during pre-commit to avoid wildcard when pre-commit is run
- Handle exception with WolframAlpha

- Logging suppression has to happen before cv2 module is imported

4.6.4 (08/18/2021)
------------------
- Move `opencv` to module level import

4.6.3 (08/16/2021)
------------------
- Bug fix on repeated ack message
- Remove unnecessary line breaks in docstrings
- Split functions wrapped within other functions
- Update docs

4.6.2 (08/15/2021)
------------------
- Remove `STATUS` and replace with `STOPPER` instead
- Restart in case of `RuntimeError`
- No long messages when heard `Good Night`
- Call `celebrate()` instead of assigning to a variable
- Increase `seconds` on `morning()` to 10
- Remove `stop` from stopping words

4.6.1 (08/09/2021)
------------------
- Reduce redundancy to avoid multiple listeners
- Raise `KeyboardInterrupt` instead of dupe methods
- Update docs from previous changes

4.6.0 (08/08/2021)
------------------
- Run `meetings()` in `time_travel()` on weekdays
- Change variables and method names

4.5.9 (08/07/2021)
------------------
- Add a `morning` method for auto alarms on weekdays at `7:00 AM`
- Reduce `regex` and variable usage
- Add a new badge to README.md

4.5.8 (08/07/2021)
------------------
- Add an `EndpointFilter` to suppress `/docs` logs from `Access` logs

4.5.7 (08/05/2021)
------------------
- Update `__main__` functions, `logger` info and `README.md`

4.5.6 (08/03/2021)
------------------
- Update doc strings and `codify` references

4.5.5 (08/02/2021)
------------------
- Handle `ConnectionResetError` from tv_controls.py
- Change logging format and add more loggers

4.5.4 (08/02/2021)
------------------
- Split active listener into a dedicated function to improve response time
- Beta test - Let Jarvis run until stopped
- Some other sanity clean up

4.5.3 (08/02/2021)
------------------
- Use `.env` to load config and remove all references to `AWS`
- Add `env vars` usage in README.md
- Remove unnecessary .py files for credentials.
- Sort the way credentials are being set when rotated.

4.5.2 (08/02/2021)
------------------
- Encode and decode the passphrase for offline comm
- Trigger uvicorn the right way
- Handle RuntimeError in offline comm
- Default new lines in notify()
- Add credentials.py to .gitignore

4.5.1 (08/01/2021)
------------------
- Update `code-block` and `hyperlinks`
- Undo the unspecified changes done on `calendar.scpt` by ScriptEditor

4.5.0 (07/31/2021)
------------------
- FEATURE::Jarvis uses `FastAPI` for offline request
- Updated docs
- Remove unwanted references
- Reduce thread count on google home connections

4.4.9 (07/28/2021)
------------------
- Windows Support Deprecated

4.4.8 (07/25/2021)
------------------
- Remove `place_holder` variables used only for recursion
- Update installs.sh, alarm.py and docs

4.4.7 (07/23/2021)
------------------
- Add missed source files

4.4.6 (07/23/2021)
------------------
- Add markdown support for sphinx documentation

4.4.5 (07/23/2021)
------------------
- Add windows support deprecation notice and dev stats

4.4.4 (07/23/2021)
------------------
- Sunset emailer.py and use `gmail-connector` instead
- Disable logging for imported modules
- Setup github actions for docs
- Update installs.sh and installs_windows.sh
- Update docs

4.4.3 (07/23/2021)
------------------
- Setup github actions for docs

4.4.2 (07/22/2021)
------------------
- Add FaceRecognition setup for Windows
- Ignore dot (.) files within `train` directory
- Update installs_windows.sh
- Move appscript imports to PersonalCloud to avoid import errors on windows
- Fix filename for logs

4.4.1 (07/18/2021)
------------------
- Modify terminating PIDs for PersonalCloud
- Quote env var for personal_cloud_host
- Update docs

4.4.0 (07/12/2021)
------------------
- Remove volume functionality for PersonalCloud
- Check if volume exists
- Update docs and README.md

4.3.9 (07/11/2021)
------------------
- Fail proofing and adapt changes in personal_cloud
- Update logger.py to new log name
- Add hyperlinks in docstrings
- Modify main module in ip_scanner.py

4.3.8 (07/10/2021)
------------------
- Add and update list comprehensions

4.3.7 (07/10/2021)
------------------
- Have one static file for alarm
- Update doc strings

4.3.6 (07/10/2021)
------------------
- Add more badges

4.3.5 (07/10/2021)
------------------
- add main module for ip scanner

4.3.4 (07/02/2021)
------------------
- bug fix on devices.html and update .gitignore

4.3.3 (07/02/2021)
------------------
- Fix for hostnames carrying .local at the end

4.3.2 (07/02/2021)
------------------
- Add voice-controlled device selector using html display
- Bug fixes
- Update docs

4.3.1 (07/02/2021)
------------------
- Say a message when a device is asked to choose.
- More additions on docs

4.3.0 (07/02/2021)
------------------
- Remove theme.css as we are using html_theme_options in conf.py

4.2.9 (07/02/2021)
------------------
- Use pick module to locate the right device
- Increase docs page width.
- Update <code> in docstrings.
- Specify Notes and See Also sections in docs.

4.2.8 (06/29/2021)
------------------
- Fix typo, missing not 'meetings' file in path.isfile

4.2.7 (06/27/2021)
------------------
- store empty dict if tv_client_key is None
- params.json -> credentials.json
- Run indicators in a Thread
- Update .gitignore
- Update docs

4.2.6 (06/27/2021)
------------------
- Add hinting and return type for docs
- Fix logs directory setup for docs
- Increase volume during alarm and revert after 60 seconds

4.2.5 (06/26/2021)
------------------
- Read/create params.json to get credentials locally

4.2.4 (06/26/2021)
------------------
- fix some misinterpretations and use wake_up2 once again

4.2.3 (06/26/2021)
------------------
- bug fixes on meetings and add more info to logging

4.2.2 (06/25/2021)
------------------
- purge old log files during start up, update docs

4.2.1 (06/25/2021)
------------------
- Maintain docs pattern throughout

4.2.0 (06/25/2021)
------------------
- Solve wait time on meetings
- Fix bug that was breaking meetings
- Update .gitignore and docs

4.1.9 (06/24/2021)
------------------
- FEATURE::Jarvis can now read the calendar too

4.1.8 (06/24/2021)
------------------
- rename apple scripts and move tv notifications to indicators

4.1.7 (06/24/2021)
------------------
- Lock screen when said good night
- Notify when parameters are updated
- Add new mp3 when tv ip scan initiates
- Update README.md and docs

4.1.6 (06/23/2021)
------------------
- call class instance instead of reusing class name

4.1.5 (06/23/2021)
------------------
- update README.md

4.1.4 (06/14/2021)
------------------
- change temperature.py to class module and update docs

4.1.3 (06/14/2021)
------------------
- split modules in table of contents

4.1.2 (06/14/2021)
------------------
- change docs theme and add new classes

4.1.1 (06/13/2021)
------------------
- format doc strings for bulleted lists

4.1.0 (06/13/2021)
------------------
- onboard sphinx docs

4.0.9 (06/13/2021)
------------------
- update function and method arguments to specific datatype
- update .gitignore

4.0.8 (06/13/2021)
------------------
- follow coding standards mentioned in README.md

4.0.7 (06/13/2021)
------------------
- fix occasional threadtimeouterror
- respond only to Jarvis

4.0.6 (06/06/2021)
------------------
- FEATURE::Jarvis can now alter brightness of lights
- Remove threading for functions taking multiple args
- Catch TimeoutError on offline_communicator
- Fix tonight to goodnight in wake up messages

4.0.5 (05/26/2021)
------------------
- fix intermittent index errors in meetings, set timeout to read outlook

4.0.4 (05/23/2021)
------------------
- reduce redundancy on AWSClients

4.0.3 (05/23/2021)
------------------
- remove unnecessary calls to aws and use ip scanner instead
- add bedroom lights
- handle exception with arp command

4.0.2 (05/23/2021)
------------------
- retain socket timeout at 30 seconds and reduce recursion limit

4.0.1 (05/22/2021)
------------------
- remove mandatory sleep time

4.0.0 (05/22/2021)
------------------
- check devices connected before using IPs
- update requirements and doc strings
- update README.md
- update tv_connect.mp3

3.9.9 (05/21/2021)
------------------
- FEATURE::Jarvis can now fix old creds in aws and log outdated env vars
- automate client key process in TV features

3.9.8 (05/21/2021)
------------------
- FEATURE::Jarvis scans localhost devices for IP to avoid outdated IPs in ENV VARs

3.9.7 (05/21/2021)
------------------
- reload logging module before using it - fixes intermittent issues with logger

3.9.6 (05/20/2021)
------------------
- remove defined sleep time for events while triggering personal cloud

3.9.5 (05/20/2021)
------------------
- remove hard check for keyword and increase threshold

3.9.4 (05/19/2021)
------------------
- shuffle imports to specifics

3.9.3 (05/04/2021)
------------------
- Logger to log in a dedicated directory for easy research

3.9.2 (05/04/2021)
------------------
- Use walrus operator to reduce variable assignment, catch connection error, remove location.yaml only if found

3.9.1 (04/30/2021)
------------------
- FEATURE::Jarvis can dynamically choose an allowed TCP port that isn't used

3.9.0 (04/30/2021)
------------------
- FEATURE::Jarvis can now mount and unmount a volume if the volume is connected

3.8.9 (04/30/2021)
------------------
- fix logger level to be more accurate

3.8.8 (04/30/2021)
------------------
- kill ngrok process and delete repo during disable, personal_cloud setup runs simultaneously

3.8.7 (04/30/2021)
------------------
- include 'if not' for walrus operators, store root password a primary variable

3.8.6 (04/30/2021)
------------------
- change datetime format in logger.py

3.8.5 (04/30/2021)
------------------
- log function name, line number and log level, default log level to FATAL, ERROR and CRITICAL

3.8.4 (04/30/2021)
------------------
- reformat lights.py

3.8.3 (04/29/2021)
------------------
- FEATURE::Jarvis can now trigger ngrok to open a tunnel for personal cloud
- Avoids the risk of always having a port open and manually enabling ngrok

3.8.2 (04/28/2021)
------------------
- FEATURE::Jarvis can now track the modified time of location.yaml and keep updating it every 72 hours
- reduce threshold

3.8.1 (04/28/2021)
------------------
- bring back long lost volume controller command line utility for windows

3.8.0 (04/28/2021)
------------------
- FEATURE::Jarvis can now store your location info as a yaml file and reuse it
- This avoids too many calls to pyicloud library and reduces notification on apple devices

3.7.9 (04/28/2021)
------------------
- dump unrecognized data to training_data.yaml in a thread to save response time

3.7.8 (04/28/2021)
------------------
- dump unrecognized data to yaml file prior regardless of google results' status

3.7.7 (04/28/2021)
------------------
- add some badges and update runbook

3.7.6 (04/27/2021)
------------------
- FEATURE::Jarvis can now change the smart light colors

3.7.5 (04/26/2021)
------------------
- FEATURE::Jarvis can now enable or disable personal cloud in a much secured way

3.7.4 (04/24/2021)
------------------
- remove unnecessary variable declaration

3.7.3 (04/24/2021)
------------------
- switch to static methods to reduce memory usage
- because python doesn't have to instantiate a bound-method for each object instantiated

3.7.2 (04/24/2021)
------------------
- place_holder::describe each method before migrating to static

3.7.1 (04/24/2021)
------------------
- place_holder::filter methods that have only one worded elements

3.7.0 (04/23/2021)
------------------
- suppress console output that were missed earlier

3.6.9 (04/22/2021)
------------------
- fix ip getting picked incorrectly

3.6.8 (04/22/2021)
------------------
- execute command instead of checking output and hide stderr

3.6.7 (04/19/2021)
------------------
- FEATURE::Jarvis can now get the public IP address along with connection SSID for potential remote connections through TCP

3.6.6 (04/18/2021)
------------------
- replace repeated .lower() with a variable

3.6.5 (04/18/2021)
------------------
- break loop in renew() in case of keywords from sleep()

3.6.4 (04/17/2021)
------------------
- play start up sound in a thread
- update doc strings for offline communicator

3.6.3 (04/17/2021)
------------------
- FEATURE::Jarvis can perform a screen lock instead of sleep
- Fix iPhone 10 look up failure

3.6.2 (04/11/2021)
------------------
- FEATURE::Jarvis can now put the device on sleep
- restart in case of RunTime Error
- speed test lat and lon to be a tuple
- Jarvis to respond to greetings even during late nights

3.6.1 (04/10/2021)
------------------
- revisit listener timings

3.6.0 (04/09/2021)
------------------
- Update speed test library to the latest release version

3.5.9 (04/09/2021)
------------------
- overcome connection issues with Speedtest module

3.5.8 (04/07/2021)
------------------
- FEATURE::Jarvis can now restart the host and suggest a restart if boot time is too long

3.5.7 (04/07/2021)
------------------
- bug fix on potential exceptions

3.5.6 (04/04/2021)
------------------
- Use multiprocessing for meetings to reduce osascript wait time

3.5.5 (04/04/2021)
------------------
- Kill PIDs for terminals interrupting shutdown

3.5.4 (04/04/2021)
------------------
- Request shutdown in case of high boot time

3.5.3 (04/04/2021)
------------------
- Use Address Resolution Protocol to get TV's mac address
- Reduce threshold to minimize caching

3.5.2 (03/30/2021)
------------------
- ring the device first, and then get ack for location info

3.5.1 (03/30/2021)
------------------
- Fix occasional runtime error when restart and offline_communicator run in parallel

3.5.0 (03/30/2021)
------------------
- use spindump for older Macs to get system vitals - avoids error message on screen
- add todo and address bug in locate_places()

3.4.9 (03/30/2021)
------------------
- add doc strings and remove unused temperature conversions

- faster access to env var (os.getenv to os.environ.get)
- changed pytemperature from external to local module

3.4.8 (03/28/2021)
------------------
- FEATURE::Jarvis can now tell the system vitals like with fan speed and CPU/GPU temperature and boot time

3.4.7 (03/25/2021)
------------------
- auto connect to TV on commands other than 'turn off'

3.4.6 (03/25/2021)
------------------
- check app availability before trying to open

3.4.5 (03/25/2021)
------------------
- reformat imports to be module specific

3.4.4 (03/25/2021)
------------------
- reformat imports to module specific

3.4.3 (03/23/2021)
------------------
- implement concurrent threads on light controls for instant response

3.4.2 (03/19/2021)
------------------
- check for git installation in multiple locations

3.4.1 (03/17/2021)
------------------
- remove new lines from email subject and catch more exceptions in J

3.4.0 (03/04/2021)
------------------
- decode email sender

3.3.9 (02/28/2021)
------------------
- send detailed notification for offline communication

3.3.8 (02/28/2021)
------------------
- optimize imports
- restructure logger file
- onboard wolfram alpha

3.3.7 (02/26/2021)
------------------
- generic way to delete lock files and avoid exception handlers for filenotfound errors

3.3.6 (02/21/2021)
------------------
- much clear logging

3.3.5 (02/20/2021)
------------------
- maintains mandatory bed time window being unresponsive
- and fix some glitches

3.3.4 (02/20/2021)
------------------
- FEATURE::Change voices on demand with custom voice modules available on your device

3.3.3 (02/20/2021)
------------------
- log failed operation for smart lights

3.3.2 (02/17/2021)
------------------
- good bye dummy()

3.3.1 (02/17/2021)
------------------
- ignore non ascii convertibles to avoid UnicodeEncodeError with symbols

3.3.0 (02/16/2021)
------------------
- free up some variable space in case of a VPN connection

3.2.9 (02/16/2021)
------------------
- say IP address when asked

3.2.8 (02/16/2021)
------------------
- bug fix on some one liners

3.2.7 (02/16/2021)
------------------
- store lights' IP as env var and ssm param

3.2.6 (02/14/2021)
------------------
- fix None type after removing J's reference words

3.2.5 (02/13/2021)
------------------
- Simplify to reduce response time and remove some redundancies

3.2.4 (02/06/2021)
------------------
- fix case sensitiveness in TV and spotted bug in meetings

3.2.3 (02/06/2021)
------------------
- FEATURE::Jarvis can now keep you informed about meetings/appointments
- Use apple script to access calendar events
- add coin flip sound
- refactor subprocess utilization

3.2.2 (02/06/2021)
------------------
- offline thread will run on single login session
- dedicated function for sms send
- scrap communicator.py
- improve coding standards

3.2.1 (02/05/2021)
------------------
- include traceback for offline communicator and insert timed wait instead of restart during an error

3.2.0 (02/01/2021)
------------------
- remove recurring .replace()

3.1.9 (02/01/2021)
------------------
- set default timeout for imaplib using sockets, purge emails and logout after reading

3.1.8 (02/01/2021)
------------------
- include traceback, increase timed wait after response in offline communicator and fix lower case issues

3.1.7 (01/29/2021)
------------------
- FEATURE::PR raised by @ariv797

3.1.6 (01/29/2021)
------------------
- restart when issues with offline communicator and handle lock file deletion gracefully

3.1.5 (01/29/2021)
------------------
- Improve search_engine_parser to get best results from google

3.1.4 (01/29/2021)
------------------
- Refactor Security Mode and gather all env vars in one place

3.1.3 (01/25/2021)
------------------
- FEATURE::Jarvis can now be accessed from anywhere in the world
- FYI::Read doc string for offline communicator
- improved logging and dedicated logger file

3.1.2 (01/21/2021)
------------------
- add more smart lights' host ids and some more optimization

3.1.1 (01/20/2021)
------------------
- FEATURE::Jarvis can now control smart lights around you
- Added a dedicated localhost checker and reverted phrase time limit

3.1.0 (01/19/2021)
------------------
- BETA::Compile multiple asks with 'and' and 'also', remove phrase time limit (tentative)

3.0.9 (01/18/2021)
------------------
- hostname of the machine will be looked up for location services

3.0.8 (01/15/2021)
------------------
- minor bug fixes
- reminders were incomplete for words like private as it has an 'at' in the string
- messages were sent only when an entire statement is heard along with the message and number

3.0.7 (01/05/2021)
------------------
- change static methods to instance methods and some minor optimizations

3.0.6 (01/05/2021)
------------------
- Use MultiThreading and scan the whole IP range for GoogleHome devices and comma_separator for meaningful sentences given a list

3.0.5 (01/05/2021)
------------------
- add comments and revert some changes on sentry_mode()

3.0.4 (01/05/2021)
------------------
- use while loop to reduce function calls and global variables

3.0.3 (01/03/2021)
------------------
- Bug fix for session time out and reused location when tracking apple devices

3.0.2 (01/02/2021)
------------------
- FEATURE::Jarvis can now locate, ring and enable lost mode on, any of your Apple devices

3.0.1 (01/02/2021)
------------------
- added some more improvements and TODOs

3.0.0 (12/30/2020)
------------------
- get rid of old regex searches, fix place name for weather_condition and remove timeout=None

2.9.9 (12/29/2020)
------------------
- Feature::Jarvis can now guard your surroundings when you are away

2.9.8 (12/26/2020)
------------------
- save lock file as reminder message to avoid loosing it during restart

2.9.7 (12/26/2020)
------------------
- Jarvis will log restarting times from now

2.9.6 (12/25/2020)
------------------
- major refactor and add celebration wishes at more places

2.9.5 (12/25/2020)
------------------
- use volume_controller() to modify volume and reduce code redundancy

2.9.4 (12/25/2020)
------------------
- FEATURE::Jarvis can now wish on events/festivals/birthdays

2.9.3 (12/25/2020)
------------------
- auto adjust brightness with current time and custom brightness level and some more improvements

2.9.2 (12/23/2020)
------------------
- FEATURE::Jarvis can now alter screen brightness
- Use size_converter() to avoid manual bytes conversion

2.9.1 (12/23/2020)
------------------
- Remove punctuator because of less usage and more start up time

2.9.0 (12/21/2020)
------------------
- clean up some left overs

2.8.9 (12/20/2020)
------------------
- remove exception handler for recursion

2.8.8 (12/20/2020)
------------------
- update .gitignore

2.8.7 (12/15/2020)
------------------
- dedicated function for listener to reduce code redundancy

2.8.6 (12/14/2020)
------------------
- add some returns to avoid too much method overloading

2.8.5 (12/10/2020)
------------------
- because 3 conditions take more time than 1

2.8.4 (12/09/2020)
------------------
- dedicated function for greeting and setup weekday routine

2.8.3 (12/08/2020)
------------------
- setup daily default startup

2.8.2 (12/07/2020)
------------------
- avoid repeated function calls and wrap up into a while

2.8.1 (12/05/2020)
------------------
- dedicated exit_process() to reduce code redundancy
- alarm and reminder check upon exit

2.8.0 (12/05/2020)
------------------
- some more exception handling

2.7.9 (12/04/2020)
------------------
- complete TODO items and pep8 on some spells

2.7.8 (12/04/2020)
------------------
- Fix some condition blocks and exception handlers

2.7.7 (11/29/2020)
------------------
- Fix some mess I did earlier

2.7.6 (11/28/2020)
------------------
- Install git automatically if not found on machine

2.7.5 (11/28/2020)
------------------
- Bypass initialize and update blueutil installation from source

2.7.4 (11/28/2020)
------------------
- More stable bluetooth connections and response

2.7.3 (11/27/2020)
------------------
- FEATURE::Jarvis can now scan and connect to bluetooth devices

2.7.2 (11/27/2020)
------------------
- remove few exception handlers and reduce redundancy

2.7.1 (11/23/2020)
------------------
- increase threshold and use random acknowledgement message

2.7.0 (11/22/2020)
------------------
- Jarvis no longer relies on icloud api for location services

2.6.9 (11/22/2020)
------------------
- FEATURE::Introduce conditional weather report which includes specific part of a day

2.6.8 (11/22/2020)
------------------
- rephrase a bit

2.6.7 (11/21/2020)
------------------
- Jarvis can now help with spellings and forked git repos

2.6.6 (11/21/2020)
------------------
- install 2 versions of sqlalchemy for Windows to support chatterbot
-2 - support chatbot
-3.6 - handle time.clock() removal in python 3.8

2.6.5 (11/21/2020)
------------------
- FEATURE::Jarvis can now get your internet speed

2.6.4 (11/21/2020)
------------------
- Jarvis can now restart himself
- Fatal Python error::Cannot recover from stack overflow

2.6.3 (11/20/2020)
------------------
- catch more exceptions and modify keywords

2.6.2 (11/17/2020)
------------------
- create train dir to avoid an exception handler
- don't decode emails with no subject
- remove exception handler for PST vs PDT

2.6.1 (11/17/2020)
------------------
- read camera output before deciding which camera to choose

2.6.0 (11/17/2020)
------------------
- FEATURES::1. Face Recognition model will now learn from unrecognized/new faces by storing it with a name
- Look for camera errors and catch exception when no cameras are found

2.5.9 (11/16/2020)
------------------
- FEATURE::Jarvis can now detect faces using open-cv and hog model (Histogram Oriented Gradients)
- Read wiki for setup instructions

2.5.8 (11/16/2020)
------------------
- FEATURE::Jarvis can now detect faces using open-cv and hog model (Histogram Oriented Gradients)
- Read wiki for setup instructions

2.5.7 (11/16/2020)
------------------
- remove some run and wait statements

2.5.6 (11/16/2020)
------------------
- catch some more exceptions, add suggestions based on weather and isolate time_travel()

2.5.5 (11/16/2020)
------------------
- Jarvis can now control PC's master volume via voice commands

2.5.4 (11/16/2020)
------------------
- update windows installation guide

2.5.3 (11/15/2020)
------------------
- roll back an unnecessary change

2.5.2 (11/15/2020)
------------------
- quick heads up from sentry mode and open url via google search parser

2.5.1 (11/14/2020)
------------------
- add precise location for iPhone
- handle more exceptions
- getting rid of some useless statements

2.5.0 (11/14/2020)
------------------
- dedicated exit messages to avoid old messages

2.4.9 (11/13/2020)
------------------
- update version specific requirements

2.4.8 (11/12/2020)
------------------
- one source for microphone to remove code redundancies and follow PEP 8 standards

2.4.7 (11/12/2020)
------------------
- Don't try to connect TV unless asked to. Waiting for an error to handle is exhausting.

2.4.6 (11/12/2020)
------------------
- FEATURE::Jarvis can now access your WebOS TV and perform almost all necessary tasks

2.4.5 (11/10/2020)
------------------
- modify meanings from keys() to items() and change audio files for listener response

2.4.4 (11/10/2020)
------------------
- disable logging from imported modules and some other petty updates

2.4.3 (11/08/2020)
------------------
- open webpages directly

2.4.2 (11/08/2020)
------------------
- include google search option

2.4.1 (11/08/2020)
------------------
- remove redundant key words and rearrange conditions

2.4.0 (11/08/2020)
------------------
- Jarvis can now play your local music on other google speakers

2.3.9 (11/08/2020)
------------------
- check if number is integer and get confirmation before sending

2.3.8 (11/07/2020)
------------------
- Jarvis can now send messages

2.3.7 (11/07/2020)
------------------
- avoid ipinfo.io/json and use iphone location instead for precise location

2.3.6 (11/07/2020)
------------------
- No more watching the screen, Jarvis beeps when listener is ready

2.3.5 (11/07/2020)
------------------
- modify git api endpoint to include private, licensed and archived repositories

2.3.4 (11/06/2020)
------------------
- blunder fix

2.3.3 (11/06/2020)
------------------
- integrate github and let Jarvis clone repositories

2.3.2 (11/05/2020)
------------------
- increase recursion limit and handle maximum recursion depth
- RecursionError: maximum recursion depth exceeded while calling a Python object

2.3.1 (11/05/2020)
------------------
- store all env variables in ssm for cross PC access

2.3.0 (11/05/2020)
------------------
- fix typo and update installs file

2.2.9 (11/04/2020)
------------------
- make better use of search engine parser and avoid infinite loop

2.2.8 (11/02/2020)
------------------
- mute the model file download progress

2.2.7 (11/02/2020)
------------------
- auto download model file if unavailable and update requirements

2.2.6 (11/02/2020)
------------------
- long weather reports only when report is called

2.2.5 (11/01/2020)
------------------
- avoid using regex for word match and modify some keywords

2.2.4 (11/01/2020)
------------------
- delete model file and link in wiki

2.2.3 (11/01/2020)
------------------
- use pre trained model for punctuations to make Jarvis' english better

2.2.2 (11/01/2020)
------------------
- use word ninja to add proper spacing between words in a sentences

2.2.1 (11/01/2020)
------------------
- use google search parser to speak results before opening a browser

2.2.0 (10/30/2020)
------------------
- notify even on current machine during a reminder

2.1.9 (10/30/2020)
------------------
- include an option to take notes, separate sleep keywords and add comments

2.1.8 (10/30/2020)
------------------
- include city and state while saying the current time

2.1.7 (10/30/2020)
------------------
- Jarvis can now say the weather at any location

2.1.6 (10/30/2020)
------------------
- update installs to support timezones

2.1.5 (10/30/2020)
------------------
- Jarvis can now say the time at any location

2.1.4 (10/30/2020)
------------------
- add missing keyword

2.1.3 (10/28/2020)
------------------
- create a dummy function to reset waiter count

2.1.2 (10/28/2020)
------------------
- changes on response to maps_api and use geopy to calculate distance

2.1.1 (10/28/2020)
------------------
- Use google's places api before considering unprocessed

2.1.0 (10/26/2020)
------------------
- use os._exit to exit active threads

2.0.9 (10/25/2020)
------------------
- Jarvis can now set reminders and send the reminder to your phone

2.0.8 (10/25/2020)
------------------
- replicate alarm to reminder

2.0.7 (10/23/2020)
------------------
- delete lock files by count instead of alarms in current session

2.0.6 (10/23/2020)
------------------
- kill alarm thread upon exit to avoid hanging threads

2.0.5 (10/18/2020)
------------------
- update code comments

2.0.4 (10/17/2020)
------------------
- create and update yaml file for training and modifications

2.0.3 (10/17/2020)
------------------
- improve conversations

2.0.2 (10/17/2020)
------------------
- rename lock file

2.0.1 (10/17/2020)
------------------
- Jarvis can now tell jokes

2.0.0 (10/17/2020)
------------------
- update installs

1.9.9 (10/17/2020)
------------------
- list google home devices in ip range

1.9.8 (10/17/2020)
------------------
- find google home devices in a specific ip range

1.9.7 (10/17/2020)
------------------
- get ip of local machine for google home integration

1.9.6 (10/15/2020)
------------------
- Jarvis can now shutdown a machine

1.9.5 (10/14/2020)
------------------
- create lock files to remove alarms and check for lock  file before triggering an alarm

1.9.4 (10/14/2020)
------------------
- upload mp3 files for alarm

1.9.3 (10/14/2020)
------------------
- try stopping an upcoming alarm using thread id

1.9.2 (10/13/2020)
------------------
- stop an upcoming alarm

1.9.1 (10/13/2020)
------------------
- stop an upcoming alarm

1.9.0 (10/13/2020)
------------------
- pick random alarm tones handle file not found exception

1.8.9 (10/12/2020)
------------------
- change regex statement to extract alarm time

1.8.8 (10/12/2020)
------------------
- change code block to inline code for each command

1.8.7 (10/12/2020)
------------------
- extract alarm time using digit specifier (regex)

1.8.6 (10/12/2020)
------------------
- Jarvis can now set alarms in the BACKGROUND

1.8.5 (10/12/2020)
------------------
- alarm script using threading to run alarm in the background

1.8.4 (10/12/2020)
------------------
- add keywords for alarm and shutdown

1.8.3 (10/11/2020)
------------------
- go to renew instead of sleep

1.8.2 (10/11/2020)
------------------
- remove ambient noise adjuster

1.8.1 (10/11/2020)
------------------
- no more renew message
- remove is there anything message
- waits for a minute and goes to sleep
- a minute is calculated by number of times failed iteration is present

1.8.0 (10/11/2020)
------------------
- Jarvis can get directions now

1.7.9 (10/11/2020)
------------------
- additional check for place name before looking for anything after 'is'

1.7.8 (10/11/2020)
------------------
- Jarvis can now tell "where is" a particular place

1.7.7 (10/10/2020)
------------------
- tricky way to calculate distance between places and from your location

1.7.6 (10/10/2020)
------------------
- use index values to calculate distance between places

1.7.5 (10/10/2020)
------------------
- Jarvis can now tell how far you are from a place (in miles)

1.7.4 (10/10/2020)
------------------
- some more customizations

1.7.3 (10/10/2020)
------------------
- avoid \n to remove stdout

1.7.2 (10/09/2020)
------------------
- greet only on the first run using greet_check

1.7.1 (10/08/2020)
------------------
- remove cents from investment summary

1.7.0 (10/08/2020)
------------------
- more optimizations towards sentry mode

1.6.9 (10/08/2020)
------------------
- use place holder to avoid going to sentry mode unnecessarily

1.6.8 (10/08/2020)
------------------
- modify all functions with respect to sentry mode

1.6.7 (10/08/2020)
------------------
- put Jarvis on sentry mode

1.6.6 (10/08/2020)
------------------
- update .gitignore to avoid docker trials

1.6.5 (10/07/2020)
------------------
- include phone's status along with location

1.6.4 (10/07/2020)
------------------
- todo to to-do

1.6.3 (10/06/2020)
------------------
- adjust afternoon and evening greetings

1.6.2 (10/04/2020)
------------------
- modifications on adding to-do items

1.6.1 (10/04/2020)
------------------
- remove unnecessary installations

1.6.0 (10/04/2020)
------------------
- update exit keywords

1.5.9 (10/03/2020)
------------------
- build some conversation

1.5.8 (10/03/2020)
------------------
- refactor files

1.5.7 (10/03/2020)
------------------
- reconfigure os info

1.5.6 (10/02/2020)
------------------
- add ambient noise adjuster

1.5.5 (10/01/2020)
------------------
- conda install PyAudio failed on me

1.5.4 (09/30/2020)
------------------
- reconfigure with respect to report

1.5.3 (09/30/2020)
------------------
- complete working module of todo using database

1.5.2 (09/30/2020)
------------------
- create a db via jarvis

1.5.1 (09/30/2020)
------------------
- todo::update keywords for connecting to db

1.5.0 (09/30/2020)
------------------
- update database.py to be asynchronous

1.4.9 (09/29/2020)
------------------
- include option to remove data from a table

1.4.8 (09/29/2020)
------------------
- add uploader and downloader::test data from db

1.4.7 (09/29/2020)
------------------
- code reformat for create db

1.4.6 (09/29/2020)
------------------
- create a new local database and store a sample todo list

1.4.5 (09/28/2020)
------------------
- decode email subject which was utf-8 encoded

1.4.4 (09/28/2020)
------------------
- remove global variables and look for music files only within the music folder

1.4.3 (09/28/2020)
------------------
- add email stats to report

1.4.2 (09/27/2020)
------------------
- bug fix on keywords.py

1.4.1 (09/27/2020)
------------------
- update installs_windows.sh to support meanings

1.4.0 (09/27/2020)
------------------
- some more cleanup

1.3.9 (09/27/2020)
------------------
- clean up time

1.3.8 (09/27/2020)
------------------
- reconfigure apps

1.3.7 (09/27/2020)
------------------
- update often misunderstood word for exit

1.3.6 (09/27/2020)
------------------
- reconfigure meanings of a word

1.3.5 (09/27/2020)
------------------
- Jarvis can now help with meanings of words

1.3.4 (09/27/2020)
------------------
- clean up time

1.3.3 (09/26/2020)
------------------
- Jarvis can now speak emails
- Received from name, email and receive time

1.3.2 (09/26/2020)
------------------
- reconfigure app launch

1.3.1 (09/26/2020)
------------------
- add play music for windows

1.3.0 (09/26/2020)
------------------
- Jarvis can now play music
- Done by scanning whole machine for mp3 files and randomly pick one

1.2.9 (09/26/2020)
------------------
- use dedicated file for conditional blocks

1.2.8 (09/26/2020)
------------------
- hold keywords in a dedicated file for easy modifications

1.2.7 (09/26/2020)
------------------
- add more screen flush

1.2.6 (09/25/2020)
------------------
- Jarvis can now track the an iPhone's location

1.2.5 (09/25/2020)
------------------
- update installs_windows.sh to support iphone locator on windows

1.2.4 (09/25/2020)
------------------
- Jarvis can now track the an iPhone's location

1.2.3 (09/25/2020)
------------------
- update installs.sh to support locating iPhone

1.2.2 (09/25/2020)
------------------
- Jarvis can now track the user's location

1.2.1 (09/25/2020)
------------------
- don't take to renew without getting initial response

1.2.0 (09/25/2020)
------------------
- include run time stats
- reconfigure exit_msg and listener display

1.1.9 (09/25/2020)
------------------
- stop asking for names

1.1.8 (09/24/2020)
------------------
- update screen flush

1.1.7 (09/24/2020)
------------------
- flush output often

1.1.6 (09/24/2020)
------------------
- include TODOs

1.1.5 (09/24/2020)
------------------
- reconfigure exit msg

1.1.4 (09/24/2020)
------------------
- update README.md

1.1.3 (09/23/2020)
------------------
- reduce speach rate for windows

1.1.2 (09/23/2020)
------------------
- write some more info

1.1.1 (09/23/2020)
------------------
- include keywords to exit Jarvis

1.1.0 (09/21/2020)
------------------
- open windows apps via start command in cmd

1.0.9 (09/21/2020)
------------------
- use default browser instead of chrome_path

1.0.8 (09/21/2020)
------------------
- remove logger

1.0.7 (09/21/2020)
------------------
- get rid of automation as class IDs are not static or reliable

1.0.6 (09/21/2020)
------------------
- remove chromedriver and selenium

1.0.5 (09/21/2020)
------------------
- reconfigure renew function

1.0.4 (09/21/2020)
------------------
- check for brew installation status before installing

1.0.3 (09/21/2020)
------------------
- use dummy in all functions calling renew

1.0.2 (09/21/2020)
------------------
- open apps using regex and change some keywords

1.0.1 (09/21/2020)
------------------
- include dummy function for varied response

1.0.0 (09/21/2020)
------------------
- added exception handlers for unprocessed text from microphone
- INFO: Jarvis never exits when unable to process the command

0.9.9 (09/21/2020)
------------------
- use chrome driver to automate else part

0.9.8 (09/20/2020)
------------------
- so much of a hacky way to install chromedriver

0.9.7 (09/20/2020)
------------------
- reduce code redundancy

0.9.6 (09/20/2020)
------------------
- update windows support for chatbot

0.9.5 (09/20/2020)
------------------
- update installs_windows.sh to support chatbot

0.9.4 (09/19/2020)
------------------
- don't repeat what you heard

0.9.3 (09/19/2020)
------------------
- don't accidentally open incorrect searches

0.9.2 (09/19/2020)
------------------
- don't repeat what you heard

0.9.1 (09/19/2020)
------------------
- look up google instead of not configured message

0.9.0 (09/19/2020)
------------------
- update installs.sh to support chat bot

0.8.9 (09/19/2020)
------------------
- restructure code

0.8.8 (09/19/2020)
------------------
- remove training modules upon exiting chat bot

0.8.7 (09/19/2020)
------------------
- add feature to exit from chat bot

0.8.6 (09/19/2020)
------------------
- avoid repeated model trainings

0.8.5 (09/19/2020)
------------------
- ignore bad response from chat bot

0.8.4 (09/19/2020)
------------------
- inform when bot is ready

0.8.3 (09/19/2020)
------------------
- integrate chat bot with jarvis

0.8.2 (09/17/2020)
------------------
- add LICENSE

0.8.1 (09/16/2020)
------------------
- reduce response time

0.8.0 (09/16/2020)
------------------
- update README.md

0.7.9 (09/16/2020)
------------------
- update README.md

0.7.8 (09/16/2020)
------------------
- increase time limit for repeater

0.7.7 (09/16/2020)
------------------
- open webpages on windows OS

0.7.6 (09/16/2020)
------------------
- speak out error message for windows

0.7.5 (09/16/2020)
------------------
- add windows support for installing requirements

0.7.4 (09/16/2020)
------------------
- remove misleading keywords

0.7.3 (09/15/2020)
------------------
- respond if app is not found

0.7.2 (09/15/2020)
------------------
- look if app is available

0.7.1 (09/15/2020)
------------------
- update volume display style

0.7.0 (09/15/2020)
------------------
- write and clear screen instead of logging
- this enables user to see only one message on the screen instead of long logging information of when Jarvis is ready to listen

0.6.9 (09/15/2020)
------------------
- reduce listener wait time
- timeout - phrase has to start before this
- phrase_time_limit - jarvis will listen only until this time

0.6.8 (09/14/2020)
------------------
- remove floating values for temperature

0.6.7 (09/14/2020)
------------------
- jarvis can now open any app

0.6.6 (09/14/2020)
------------------
- news source as variable

0.6.5 (09/14/2020)
------------------
- update README.md

0.6.4 (09/14/2020)
------------------
- remove unnecessary punctuation which confuses jarvis

0.6.3 (09/13/2020)
------------------
- add repeater

0.6.2 (09/12/2020)
------------------
- trigger same function again

0.6.1 (09/10/2020)
------------------
- reconfigure jarvis and robinhood integration

0.6.0 (09/10/2020)
------------------
- add robinhood.py to integrate stock info with jarvis

0.5.9 (09/10/2020)
------------------
- update installs.sh to integrate stock investment details

0.5.8 (09/10/2020)
------------------
- explicit weather info per location

0.5.7 (09/09/2020)
------------------
- jarvis can now tell entire day's report
- used has_been_called to check if report() was triggered

0.5.6 (09/09/2020)
------------------
- jarvis can now read today's news

0.5.5 (09/09/2020)
------------------
- reformat date and alter conditions

0.5.4 (09/09/2020)
------------------
- update installs.sh - news api

0.5.3 (09/09/2020)
------------------
- add detailed weather info

0.5.2 (09/08/2020)
------------------
- adjust greetings for noon

0.5.1 (09/08/2020)
------------------
- update README.md

0.5.0 (09/08/2020)
------------------
- update README.md

0.4.9 (09/08/2020)
------------------
- added welcome note

0.4.8 (09/08/2020)
------------------
- replicate changed keywords

0.4.7 (09/08/2020)
------------------
- change some keywords

0.4.6 (09/08/2020)
------------------
- add brew to installs.sh

0.4.5 (09/08/2020)
------------------
- update installs.sh

0.4.4 (09/08/2020)
------------------
- update README.md

0.4.3 (09/08/2020)
------------------
- update .gitignore

0.4.2 (09/08/2020)
------------------
- update pip before proceeding

0.4.1 (09/08/2020)
------------------
- some more tweaks

0.4.0 (09/08/2020)
------------------
- update installs.sh

0.3.9 (09/07/2020)
------------------
- some basic tweaks

0.3.8 (09/07/2020)
------------------
- log sensible listener information

0.3.7 (09/07/2020)
------------------
- handle multiple tasks

0.3.6 (09/07/2020)
------------------
- move conditions to a separate block

0.3.5 (09/07/2020)
------------------
- address commander by name

0.3.4 (09/07/2020)
------------------
- exception handler for multiple results from wikipedia

0.3.3 (09/07/2020)
------------------
- optimize run time::remove repeated exception handlers

0.3.2 (09/07/2020)
------------------
- wait and get user confirmation before reading whole passage

0.3.1 (09/07/2020)
------------------
- get info from wikipedia

0.3.0 (09/07/2020)
------------------
- update installer

0.2.9 (09/07/2020)
------------------
- reconfigure webpage condition for reliability

0.2.8 (09/07/2020)
------------------
- jarvis/friday can now say system configuration

0.2.7 (09/07/2020)
------------------
- found a companion for jarvis ;)

0.2.6 (09/07/2020)
------------------
- more requirements updated

0.2.5 (09/07/2020)
------------------
- restructure renew()

0.2.4 (09/07/2020)
------------------
- code reformat

0.2.3 (09/07/2020)
------------------
- jarvis can help with current weather info

0.2.2 (09/07/2020)
------------------
- update installs.sh

0.2.1 (09/07/2020)
------------------
- reformat exit message

0.2.0 (09/06/2020)
------------------
- restructure initialization and continuation for convenience

0.1.9 (09/06/2020)
------------------
- end message for date and time

0.1.8 (09/06/2020)
------------------
- jarvis can tell date and time now

0.1.7 (09/06/2020)
------------------
- reformat jarvis to open webpages

0.1.6 (09/06/2020)
------------------
- open websites

0.1.5 (09/06/2020)
------------------
- open a webpage

0.1.4 (09/06/2020)
------------------
- reformat code

0.1.3 (09/06/2020)
------------------
- implement logging

0.1.2 (09/06/2020)
------------------
- add runbook in README.md

0.1.1 (09/06/2020)
------------------
- speak what you heard

0.1.0 (09/06/2020)
------------------
- include two communication

0.0.9 (09/06/2020)
------------------
- initialize jarvis

0.0.8 (09/06/2020)
------------------
- change voice and print current volume

0.0.7 (09/06/2020)
------------------
- add text2audio.py

0.0.6 (09/06/2020)
------------------
- update installs.sh for text2audio.py

0.0.5 (09/06/2020)
------------------
- include exception handler

0.0.4 (09/06/2020)
------------------
- convert audio to text

0.0.3 (09/06/2020)
------------------
- add .gitignore

0.0.2 (09/06/2020)
------------------
- include requirements in a script file

0.0.1 (09/06/2020)
------------------
- Initial commit
