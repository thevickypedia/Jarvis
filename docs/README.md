<p align="center" style="text-align: center">
  <img src="https://vigneshrao.com/Jarvis/logo.png" width="371px" height="350px">
</p>
<h2 align="center">Voice-Activated Natural Language UI</h2>

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-blue?style=for-the-badge&logo=Python)](https://python.org)

![Python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-orange)
[![Pypi-downloads](https://img.shields.io/pypi/dm/jarvis-ironman)](https://pypi.org/project/jarvis-ironman)

**Platform Supported**

![Platform](https://img.shields.io/badge/Platform-Linux|MacOS|Windows-1f425f.svg)

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

[![PyPI version shields.io](https://img.shields.io/pypi/v/jarvis-ironman)](https://pypi.org/project/jarvis-ironman)
[![Pypi-format](https://img.shields.io/pypi/format/jarvis-ironman)](https://pypi.org/project/jarvis-ironman/#files)
[![Pypi-status](https://img.shields.io/pypi/status/jarvis-ironman)](https://pypi.org/project/jarvis-ironman)

**Activity**

[![GitHub Repo created](https://img.shields.io/date/1599432310)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/y/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub last commit](https://img.shields.io/github/last-commit/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)
[![GitHub last release](https://img.shields.io/github/release-date/thevickypedia/Jarvis)](https://api.github.com/repos/thevickypedia/Jarvis)

**Development and Maintenance**

[![Active Development](https://img.shields.io/badge/Development%20Level-Actively%20Developed-success.svg)](https://github.com/thevickypedia/Jarvis)
[![Actively Maintained](https://img.shields.io/badge/Maintenance%20Level-Actively%20Maintained-success.svg)](https://github.com/thevickypedia/Jarvis)
[![Maintainer](https://img.shields.io/badge/Maintained%20By-Vignesh%20Sivanandha%20Rao-blue.svg)](https://vigneshrao.com/)

**Reach Out**

[//]: # ([![StackOverflow]&#40;https://img.shields.io/stackexchange/stackoverflow/r/13691532&#41;]&#40;https://stackoverflow.com/users/13691532/vignesh-rao&#41;)
[![ askme ](https://img.shields.io/badge/SELECT%20*%20FROM-questions-1abc9c.svg)](https://vigneshrao.com/contact)

## Kick off

> :bulb: Using a dedicated [virtual environment](https://docs.python.org/3/tutorial/venv.html) and an IDE like 
> [PyCharm](https://www.jetbrains.com/pycharm/) is highly recommended.

**Install**
```shell
python -m pip install jarvis-ironman
```

**Initiate**
```python
import jarvis


if __name__ == '__main__':
    jarvis.start()
```

## Prerequisites
   - **MacOS** <br> _Tested on **macOS High Sierra, Mojave, Catalina, Big Sur, Monterey and Ventura**_
     - `System Preferences` → `Security & Privacy` → `Privacy`
     - Click `+` sign and add the preferred `IDE` and `Terminal` in the following sections in left pane.
       - `Microphone` - **Required** to listen and respond.
       - `Accessibility` - **Required** to use key combinations for brightness and volume controls.
       - `Camera` - **[Optional]** Required only during face recognition/detection.
       - `Automation` - **Required** to control `System Events` and other apps like Outlook and Calendar.
       - `Files and Folders` **[OR]** `Full Disk Access` - **Required** for all `FileIO` operations.

   - **Linux** <br> _Tested on **Ubuntu 22.04 LTS**_
     - Store the host machine's password as the env var: `ROOT_PASSWORD`
     - Unlike macOS and Windows, `Ubuntu` does not have app specific permissions.

   - **Windows** <br> _Tested on **Windows 10**_
     - `Settings` → `Privacy`
       - `Microphone` - **Required** to listen and respond.
       - `Camera` - **[Optional]** Required only during face recognition/detection.
       - Unlike `macOS`, `Windows` pops a confirmation window to **Allow** or **Deny** access to files and folders.
     - Install [Anaconda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html#windows-installers), [VisualStudio C++ BuildTools](https://visualstudio.microsoft.com/visual-cpp-build-tools/), and [Git](https://git-scm.com/download/win/)
     - Make sure C++ build tools are installed completely and restart
     - Add anaconda/miniconda scripts location to `PATH` in Environment Variables

## Enchiridion
Handbook - [GitHub Wiki](https://github.com/thevickypedia/Jarvis/wiki)

## Coding Standards
Docstring format: [`Google`](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) <br>
Styling conventions: [`PEP 8`](https://www.python.org/dev/peps/pep-0008/) <br>
Clean code with pre-commit hooks: [`flake8`](https://flake8.pycqa.org/en/latest/) and 
[`isort`](https://pycqa.github.io/isort/)

## [Release Notes](https://github.com/thevickypedia/Jarvis/blob/master/release_notes.rst)
**Requirement**
```shell
python -m pip install gitverse
```

**Usage**
```shell
gitverse-release reverse -f release_notes.rst -t 'Release Notes'
```

## Linting
`PreCommit` will ensure linting, and the doc creation are run on every commit.

**Requirement**
```shell
pip install sphinx==5.1.1 pre-commit recommonmark
```

**Usage**
```shell
pre-commit run --all-files
```

## Pypi Package
[![pypi-module](https://img.shields.io/badge/Software%20Repository-pypi-1f425f.svg)](https://packaging.python.org/tutorials/packaging-projects/)

[https://pypi.org/project/jarvis-ironman/](https://pypi.org/project/jarvis-ironman/)

## Runbook
[![made-with-sphinx-doc](https://img.shields.io/badge/Code%20Docs-Sphinx-1f425f.svg)](https://www.sphinx-doc.org/en/master/man/sphinx-autogen.html)

[https://jarvis-docs.vigneshrao.com/](https://jarvis-docs.vigneshrao.com/)

## License & copyright

&copy; Vignesh Rao

Licensed under the [MIT License](https://github.com/thevickypedia/Jarvis/blob/master/LICENSE)
