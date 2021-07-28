[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

[![Python 3.8](https://img.shields.io/badge/python-3.8-orange.svg)](https://www.python.org/downloads/release/python-385/)
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-391/)

###### Platform Supported
![Generic badge](https://img.shields.io/badge/Platform-MacOS-1f425f.svg)

###### Language Stats
![Language count](https://img.shields.io/github/languages/count/thevickypedia/Jarvis)
![Code coverage](https://img.shields.io/github/languages/top/thevickypedia/Jarvis)

###### Repo Stats
[![GitHub Repo stars](https://img.shields.io/github/stars/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub Repo forks](https://img.shields.io/github/forks/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub Repo watchers](https://img.shields.io/github/watchers/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)

[![GitHub](https://img.shields.io/github/license/thevickypedia/Jarvis)](LICENSE)
[![GitHub repo size](https://img.shields.io/github/repo-size/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub code size](https://img.shields.io/github/languages/code-size/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![LOC](https://img.shields.io/tokei/lines/github/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)

[![GitHub Repo issues](https://img.shields.io/github/issues-closed-raw/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub Repo issues](https://img.shields.io/github/issues-raw/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub Repo pr](https://img.shields.io/github/issues-pr-closed-raw/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub Repo pr](https://img.shields.io/github/issues-pr-raw/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)

###### Code Stats
![Modules](https://img.shields.io/github/search/thevickypedia/Jarvis/module)
![Python](https://img.shields.io/github/search/thevickypedia/Jarvis/.py)
![Threads](https://img.shields.io/github/search/thevickypedia/Jarvis/thread)
![Listener](https://img.shields.io/github/search/thevickypedia/Jarvis/listener)
![Speaker](https://img.shields.io/github/search/thevickypedia/Jarvis/speaker)
![Bash](https://img.shields.io/github/search/thevickypedia/Jarvis/.sh)
![AppleScript](https://img.shields.io/github/search/thevickypedia/Jarvis/.scpt)
![Make](https://img.shields.io/github/search/thevickypedia/Jarvis/Makefile)

###### Deployments
[![docs](https://github.com/thevickypedia/Jarvis/actions/workflows/docs.yml/badge.svg)](https://thevickypedia.github.io/Jarvis/)

###### Activity
[![GitHub Repo created](https://img.shields.io/date/1599432310)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/y/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub last commit](https://img.shields.io/github/last-commit/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)

[comment]: <> (![Stackoverflow reputation]&#40;https://img.shields.io/stackexchange/stackoverflow/r/13691532&#41;)

###### Development and Maintenance
[![Active Development](https://img.shields.io/badge/Development%20Level-Actively%20Developed-success.svg)](https://github.com/thevickypedia/Jarvis)
[![Actively Maintained](https://img.shields.io/badge/Maintenance%20Level-Actively%20Maintained-success.svg)](https://github.com/thevickypedia/Jarvis)

[![Maintained](https://img.shields.io/maintenance/yes/2021)](https://api.github.com/repos/thevickypedia/Jarvis)
[![Maintainer](https://img.shields.io/badge/Maintained%20By-Vignesh%20Sivanandha%20Rao-blue.svg)](https://vigneshrao.com/)

# Jarvis
IronMan's Jarvis with python

### Setup:
   - Run the following commands in command line/terminal:
        - `cd lib && chmod +x installs.sh` - Makes [installation file](https://git.io/JBnPq) as executable.
        - `python3 -m venv venv` - Creates a virtual env named `venv`
        - `source venv/bin/activate` - Activates the virtual env `venv`
        - `which python` - Validate which python is being used. Should be the one within the virtual env `venv`
        - [`bash installs.sh`](https://git.io/JBnPq) - Installs the required libraries/modules.
        - [`python3 jarvis.py`](https://git.io/JBnPz) - BOOM, you're all set, go ahead and interact with Jarvis

### Coding Standards:
Docstring format: [`Google`](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) <br>
Styling conventions: [`PEP 8`](https://www.python.org/dev/peps/pep-0008/) <br>
Clean code with pre-commit hooks: [`flake8`](https://flake8.pycqa.org/en/latest/) and 
[`isort`](https://pycqa.github.io/isort/)

### Pre-Commit
`pre-commit` will run `flake8` and `isort` to ensure proper coding standards along with [docs_generator](gen_docs.sh) 
to update the [runbook](#Runbook)
> `pre-commit run --all-files`

### Feature(s) Implementation:
Please refer [wiki](https://github.com/thevickypedia/Jarvis/wiki) for API usage, access controls, env variables, 
features' overview and demo videos.

### Runbook:
[![made-with-sphinx-doc](https://img.shields.io/badge/Made%20with-Sphinx-1f425f.svg)](https://www.sphinx-doc.org/en/master/man/sphinx-autogen.html)

https://thevickypedia.github.io/Jarvis/

## License & copyright

&copy; Vignesh Sivanandha Rao

Licensed under the [MIT License](LICENSE)
