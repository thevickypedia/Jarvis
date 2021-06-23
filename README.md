![GitHub](https://img.shields.io/github/license/thevickypedia/Jarvis) ![GitHub repo size](https://img.shields.io/github/repo-size/thevickypedia/Jarvis) ![GitHub Repo stars](https://img.shields.io/github/stars/thevickypedia/Jarvis) ![GitHub last commit](https://img.shields.io/github/last-commit/thevickypedia/Jarvis) ![GitHub commit activity](https://img.shields.io/github/commit-activity/y/thevickypedia/Jarvis)

# Jarvis
IronMan's Jarvis with python

### Setup:
   - Run the following commands in command line/terminal:
        - `cd lib && chmod +x installs.sh` - Makes [installation file](lib/installs.sh) as executable.
        - `python3 -m venv venv` - Creates a virtual env named `venv`
        - `source venv/bin/activate` - Activates the virtual env `venv`
        - `which python` - Validate which python is being used. Should be the one within the virtual env `venv`
        - [`bash installs.sh`](lib/installs.sh) ([`bash installs_windows.sh`](lib/installs_windows.sh) for 
          [Windows OS](https://github.com/thevickypedia/Jarvis/wiki#windows-os)) - Installs the required libraries/modules.
        - [`python3 jarvis.py`](jarvis.py) - BOOM, you're all set, go ahead and interact with Jarvis

### Coding Standards:
Docstring format: [`Google`](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) <br>
Styling conventions: [`PEP 8`](https://www.python.org/dev/peps/pep-0008/) <br>
Clean code with pre-commit hooks: [`flake8`](https://flake8.pycqa.org/en/latest/) and 
[`isort`](https://pycqa.github.io/isort/)

### Pre-Commit
`pre-commit` will run `flake8` and `isort` to ensure proper coding standards along with [docs_generator](gen_docs.sh) 
to update the [runbook](#Runbook)
> Command: `pre-commit run --all-files`

### Feature(s) Implementation:
Please refer [wiki](https://github.com/thevickypedia/Jarvis/wiki) for API usage, access controls, env variables, 
features' overview and demo videos.

### Runbook:
https://thevickypedia.github.io/Jarvis/

> Generated using [`sphinx-autogen`](https://www.sphinx-doc.org/en/master/man/sphinx-autogen.html)

#### Usage:
<h6>Manual: <code>cd doc_generator && make html</code><h6>
<h6>Auto: The autodoc generation will run as part of <code>pre-commit</code></h6>

## License & copyright

&copy; Vignesh Sivanandha Rao

Licensed under the [MIT License](LICENSE)
