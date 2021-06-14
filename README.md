![GitHub](https://img.shields.io/github/license/thevickypedia/Jarvis) ![GitHub repo size](https://img.shields.io/github/repo-size/thevickypedia/Jarvis) ![GitHub Repo stars](https://img.shields.io/github/stars/thevickypedia/Jarvis) ![GitHub last commit](https://img.shields.io/github/last-commit/thevickypedia/Jarvis) ![GitHub commit activity](https://img.shields.io/github/commit-activity/y/thevickypedia/Jarvis)

# Jarvis
IronMan's Jarvis with python

### Setup:
   - Run the following commands in command line/terminal:
        - `cd lib && chmod +x installs.sh` - Makes [installation file](lib/installs.sh) as executable.
        - `python3 -m venv venv` - Creates a virtual env named `venv`
        - `source venv/bin/activate` - Activates the virtual env `venv`
        - `which python` - Validate which python is being used. Should be the one within the virtual env `venv`
        - `bash installs.sh` (`bash installs_windows.sh` for [Windows OS](https://github.com/thevickypedia/Jarvis/wiki#windows-os)) - Installs the required libraries/modules.
        - `python3 jarvis.py` - BOOM, you're all set, go ahead and interact with Jarvis

### Coding Standards:
Docstring format: `Google`<br>
Styling conventions: `PEP 8`<br>
Clean code with pre-commit hooks: `flake8` and `isort`

`pre-commit run --all-files`

### Feature(s) Implementation:
Please refer [wiki](https://github.com/thevickypedia/Jarvis/wiki) for API usage, access controls, env variables, features' overview and demo videos.

### Runbook:
https://thevickypedia.github.io/Jarvis/

Generated using `sphinx-autogen`

#### Usage:
Manual: `cd doc_generator && make html`

Auto: The autodoc generation will run as part of `pre-commit`

## License & copyright

&copy; Vignesh Sivanandha Rao

Licensed under the [MIT License](LICENSE)
