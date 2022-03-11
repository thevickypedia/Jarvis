[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)
[![ForTheBadge built-with-swag](http://ForTheBadge.com/images/badges/built-with-swag.svg)](https://github.com/thevickypedia/Jarvis)

![Python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue)

**Platform Supported**

![Generic badge](https://img.shields.io/badge/Platform-MacOS-1f425f.svg)

**Language Stats**

![Language count](https://img.shields.io/github/languages/count/thevickypedia/Jarvis)
![Code coverage](https://img.shields.io/github/languages/top/thevickypedia/Jarvis)

**Repo Stats**

[![GitHub Repo stars](https://img.shields.io/github/stars/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub Repo forks](https://img.shields.io/github/forks/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub Repo watchers](https://img.shields.io/github/watchers/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)

[![GitHub](https://img.shields.io/github/license/thevickypedia/Jarvis)](https://github.com/thevickypedia/Jarvis/blob/master/LICENSE)
[![GitHub repo size](https://img.shields.io/github/repo-size/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub code size](https://img.shields.io/github/languages/code-size/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![LOC](https://img.shields.io/tokei/lines/github/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)

[![GitHub Repo issues](https://img.shields.io/github/issues-closed-raw/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub Repo issues](https://img.shields.io/github/issues-raw/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub Repo pr](https://img.shields.io/github/issues-pr-closed-raw/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub Repo pr](https://img.shields.io/github/issues-pr-raw/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)

**Code Stats**

![Modules](https://img.shields.io/github/search/thevickypedia/Jarvis/module)
![Python](https://img.shields.io/github/search/thevickypedia/Jarvis/.py)
![Threads](https://img.shields.io/github/search/thevickypedia/Jarvis/thread)
![Listener](https://img.shields.io/github/search/thevickypedia/Jarvis/listener)
![Speaker](https://img.shields.io/github/search/thevickypedia/Jarvis/speaker)
![Bash](https://img.shields.io/github/search/thevickypedia/Jarvis/.sh)
![AppleScript](https://img.shields.io/github/search/thevickypedia/Jarvis/.scpt)
![Make](https://img.shields.io/github/search/thevickypedia/Jarvis/Makefile)

**Deployments**

[![pages-build-deployment](https://github.com/thevickypedia/Jarvis/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/thevickypedia/Jarvis/actions/workflows/pages/pages-build-deployment)
[![pypi](https://github.com/thevickypedia/Jarvis/actions/workflows/python-publish.yml/badge.svg)](https://github.com/thevickypedia/Jarvis/actions/workflows/python-publish.yml)

[![Pypi-format](https://img.shields.io/pypi/format/jarvis-ironman)](https://pypi.org/project/jarvis-ironman/#files)
[![Pypi-status](https://img.shields.io/pypi/status/jarvis-ironman)](https://pypi.org/project/jarvis-ironman)
[![sourcerank](https://img.shields.io/librariesio/sourcerank/pypi/jarvis-ironman)](https://libraries.io/pypi/jarvis-ironman)

**Activity**

[![GitHub Repo created](https://img.shields.io/date/1599432310)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/y/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub last commit](https://img.shields.io/github/last-commit/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)

**Development and Maintenance**

[![Active Development](https://img.shields.io/badge/Development%20Level-Actively%20Developed-success.svg)](https://github.com/thevickypedia/Jarvis)
[![Actively Maintained](https://img.shields.io/badge/Maintenance%20Level-Actively%20Maintained-success.svg)](https://github.com/thevickypedia/Jarvis)

[![Maintained](https://img.shields.io/maintenance/yes/2022)](https://api.github.com/repos/thevickypedia/Jarvis)
[![Maintainer](https://img.shields.io/badge/Maintained%20By-Vignesh%20Sivanandha%20Rao-blue.svg)](https://vigneshrao.com/)

**Reach Out**

[![Ask Me | Anything ](https://img.shields.io/badge/Ask%20me-Anything-1abc9c.svg)](https://vigneshrao.com/contact)

# Jarvis
IronMan's Jarvis with python

### Setup
   - Clone this [repository](https://github.com/thevickypedia/Jarvis.git) or download it from [pypi](https://pypi.org/project/jarvis-ironman/)
   - Run the following commands in command line/terminal:
        - `cd lib && chmod +x installs.sh` - Makes [installation file](https://git.io/JBnPq) as executable.
        - `python3 -m venv venv` - Creates a virtual env named `venv`
        - `source venv/bin/activate` - Activates the virtual env `venv`
        - `which python` - Validate which python is being used. Should be the one within the virtual env `venv`
        - [`bash installs.sh`](https://git.io/JBnPq) - Installs the required libraries/modules.
        - [`python3 jarvis.py`](https://git.io/JBnPz) - BOOM, you're all set, go ahead and interact with Jarvis

### ENV Variables
Environment variables are loaded from a `.env` file and validated using `pydantic`

<details>
<summary><strong>More on <a href="https://github.com/thevickypedia/Jarvis/wiki#environment-variables">Environment variables</a></strong></summary>

**Default - [Offline communicator](https://github.com/thevickypedia/Jarvis/blob/master/executors/offline.py):**
- **OFFLINE_PORT** - Port number to initiate offline communicator. Defaults to `4483`
- **OFFLINE_PASS** - Secure phrase to authenticate offline requests. Defaults to `jarvis`

**Accurate Location: (Defaults to the location based on `Public IP` which is _approximate_)**
- **ICLOUD_USER** - iCloud account username.
- **ICLOUD_PASS** - iCloud account password.

**Features**
- **GIT_USER** - GitHub Username
- **GIT_PASS** - GitHub Token
- **WEATHER_API** - API Key from [openweathermap](https://openweathermap.org/) 
- **NEWS_API** - API Key from [newsapi](https://newsapi.org/docs/client-libraries/python)
- **MAPS_API** - API Key for maps from [google](https://developers.google.com/maps/documentation/maps-static/get-api-key)
- **GMAIL_USER** - Gmail account username to send and read emails.
- **GMAIL_PASS** - Gmail account password to send and read emails.
- **ALT_GMAIL_USER** - Alternate gmail account username to send an SMS. (`gmail_user` can be re-used)
- **ALT_GMAIL_PASS** - Alternate gmail account password to send an SMS. (`gmail_pass` can be re-used)
- **RECIPIENT** - Email address to which the emails from jarvis have to be received.
- **ROBINHOOD_USER** - Robinhood account username.
- **ROBINHOOD_PASS** - Robinhood account password.
- **ROBINHOOD_QR** - Robinhood login [QR code](https://robinhood.com/account/settings)
- **BIRTHDAY** - Birth date in the format DD-MM - Example: `24-April`
- **ICLOUD_RECOVERY** - Recovery phone number to activate lost mode on a target device - Example: `+11234567890`
- **PHONE_NUMBER** - To send SMS from Jarvis - Example: `+11234567890`
- **ROOT_PASSWORD** - System password for your `mac` to get the system vitals.
- **MEETING_APP** - Application where the meetings are listed. Defaults to `calendar` but value can be `calendar` or `outlook`
- **WOLFRAM_API_KEY** - API Key from wolfram alpha.

**[VPNServer](https://github.com/thevickypedia/vpn-server) integration**
- **VPN_USERNAME** - Username to create vpn-server. Defaults to profile username or `openvpn`
- **VPN_PASSWORD** - Password to authenticate vpn-server. Defaults to profile password or `aws_vpn_2021`

**[TV](https://github.com/thevickypedia/Jarvis/blob/master/modules/tv/tv_controls.py) controls** - Applies only for [LGWebOS](https://en.wikipedia.org/wiki/WebOS)
- **TV_CLIENT_KEY** - TV's Client key. Auto-generated when used for the first time.

**[IP Scanner](https://github.com/thevickypedia/Jarvis/blob/master/modules/netgear/ip_scanner.py)** - Applies only for [Netgear routers](https://github.com/MatMaul/pynetgear#supported-routers)
- **ROUTER_PASS** - Router's admin password to get the available devices using `pynetgear` module.
     > Note that this may be done even without the module by simply using the arp table.
  > Using the module improves accuracy and support between different bandwidths since the devices are already connected to the router.

**[Car Controls](https://github.com/thevickypedia/Jarvis/blob/master/modules/car)** - Applies only for JLR vehicles using `InControl API`.
- **CAR_EMAIL** - Email address to log in to InControl API.
- **CAR_PASS** - Password to authenticate InControl API.
- **CAR_PIN** - InControl PIN.

**[Telegram Bot](https://github.com/thevickypedia/Jarvis/blob/master/executors/telegram.py) integration**
- **BOT_TOKEN** - Telegram BOT token.
- **BOT_CHAT_IDS** - UserID/ChatID for a particular user.
- **BOT_USERS** - Usernames that should have access to Jarvis.
</details>

### Smart Devices
A source file `smart_devices.yaml` is used to store smart devices' IPs. `Jarvis` supports `MagicHome` lights and `LGWebOS` TVs.

<details>
<summary><strong>Manual Setup</strong></summary>

By using `smart_devices.yaml`, the `Netgear` module can be avoided at the cost of manually updating the source file in case of IP changes.

- The source file should be as following:

```yaml
bedroom_ip:
- LOCAL_IP_ADDRESS
hallway_ip:
- LOCAL_IP_ADDRESS
kitchen_ip:
- LOCAL_IP_ADDRESS
tv_ip: LOCAL_IP_ADDRESS
tv_mac: TV_MAC_ADDRESS
```
</details>

### Automation Setup [Optional]
Executes [offline compatible](https://github.com/thevickypedia/Jarvis/blob/master/api/controller.py#L7) tasks at pre-defined times without any user interaction.
Uses an `automation.yaml` file as source.

<details>
<summary><strong>Setup Instructions</strong></summary>

The YAML file should be a dictionary within a dictionary that looks like the below.

**OPTIONAL:** The key, `day` can be a `list` of days, or a `str` of a specific day or simply a `str` saying `weekday` or
`weekend` when the particular automation should be executed.

> Not having the key `day` will run the automation daily.

```yaml
6:00 AM:
  day: weekday  # Runs only between Monday and Friday
  task: set my bedroom lights to 50%
6:30 AM:
  day:  # Runs only on Monday, Wednesday and Friday
  - Monday
  - wednesday
  - FRIDAY
  task: set my bedroom lights to 100%
8:00 AM:  # Runs only on Saturday and Sunday
  day: weekend
  task: set my bedroom lights to 100%
9:00 PM:  # Runs daily
  task: set my bedroom lights to 5%
```
</details>

### Coding Standards
Docstring format: [`Google`](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) <br>
Styling conventions: [`PEP 8`](https://www.python.org/dev/peps/pep-0008/) <br>
Clean code with pre-commit hooks: [`flake8`](https://flake8.pycqa.org/en/latest/) and 
[`isort`](https://pycqa.github.io/isort/)

### Linting
`PreCommit` will ensure linting, and the doc creation are run on every commit.

**Requirement**
<br>
`pip install --no-cache --upgrade sphinx pre-commit recommonmark`

**Usage**
<br>
`pre-commit run --all-files`

### Feature(s) Implementation
Please refer [wiki](https://github.com/thevickypedia/Jarvis/wiki) for API usage, access controls, env variables, 
features' overview and demo videos.

### Pypi Package
[![pypi-module](https://img.shields.io/badge/Software%20Repository-pypi-1f425f.svg)](https://packaging.python.org/tutorials/packaging-projects/)

[https://pypi.org/project/jarvis-ironman/](https://pypi.org/project/jarvis-ironman/)

### Runbook
[![made-with-sphinx-doc](https://img.shields.io/badge/Code%20Docs-Sphinx-1f425f.svg)](https://www.sphinx-doc.org/en/master/man/sphinx-autogen.html)

[https://thevickypedia.github.io/Jarvis/](https://thevickypedia.github.io/Jarvis/)

## License & copyright

&copy; Vignesh Sivanandha Rao

Licensed under the [MIT License](https://github.com/thevickypedia/Jarvis/blob/master/LICENSE)
