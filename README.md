<p align="center" style="text-align: center">
  <img src="https://thevickypedia.github.io/open-source/images/logo/jarvis.png" width="371px" height="350px" alt="logo">
</p>
<h2 align="center">Voice-Activated Natural Language UI</h2>

[![made-with-python][label-python]][python]

![Python][label-pyversion]
![Pypi-downloads][label-pypi-downloads]
[![OpenSSF Scorecard][label-open-ssf]][link-open-ssf]

**Platform Supported**

![Platform][label-platform]

**Language Stats**

![Language count][label-language-ct]
![Code coverage][label-code-coverage]

**[Repo Stats][repo]**

[![GitHub][label-license]][license]

![GitHub Repo stars][label-stars]
![GitHub Repo forks][label-forks]
![GitHub Repo watchers][label-watchers]

![GitHub repo size][label-repo-size]
![GitHub code size][label-code-size]
![GitHub code line][label-code-line]
![GitHub file count][label-file-count]

![GitHub Repo issues][label-issues-closed]
![GitHub Repo issues][label-issues-raw]
![GitHub Repo pr][label-pr-closed]
![GitHub Repo pr][label-pr-raw]

**Code Stats**

<!-- todo: self-host a code analyzer
![GitHub file count][label-file-count]
![GitHub lines of code][label-line-of-code]
-->

![Modules][label-stats-Modules]
![Python][label-stats-Python]
![Threads][label-stats-Threads]
![Listener][label-stats-Listener]
![Speaker][label-stats-Speaker]
![Bash][label-stats-Bash]
![AppleScript][label-stats-AppleScript]
![Make][label-stats-Make]

**Deployments**

[![pages][label-actions-pages]][gha_pages]
[![pypi][label-actions-pypi]][gha_pypi]
[![markdown][label-actions-markdown]][gha_md_valid]
[![update-release-notes][label-actions-release]][gha_release_notes]

[![Pypi][label-pypi]][pypi]
[![Pypi-format][label-pypi-format]][pypi-files]
[![Pypi-status][label-pypi-status]][pypi]

**Activity**

![GitHub Repo created][label-github-repo-created]
![GitHub commit activity][label-github-commit-activity]
![GitHub last commit][label-github-last-commit]
![GitHub last release][label-github-last-release]

**Development and Maintenance**

![Active Development][label-active-development]
![Actively Maintained][label-actively-maintained]
[![Maintainer][label-maintainer]][webpage]

**Reach Out**

[![askme][label-askme]][webpage_contact]

## Kick off

**Recommendations**

- Install `python` [3.10] or [3.11]
- Use a dedicated [virtual environment]

**Install Jarvis**
```shell
python -m pip install jarvis-ironman
```

**Install Dependencies**
```shell
jarvis install
```

**Initiate - IDE**
```python
import jarvis


if __name__ == '__main__':
    jarvis.start()
```

**Initiate - CLI**
```shell
jarvis start
```

> Use `jarvis --help` for usage instructions.

## Prerequisites
   - **MacOS** <br> _Tested on **Mojave, Catalina, Big Sur, Monterey and Ventura**_
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
     - Install [Anaconda] or [Miniconda], [VisualStudio C++ BuildTools][vcpp], and [Git][git-cli]
     - Make sure C++ build tools are installed completely and restart
     - Add anaconda/miniconda scripts location to `PATH` in Environment Variables

## Enchiridion
Handbook - [GitHub Wiki][wiki]

## Coding Standards
Docstring format: [`Google`][google-docs] <br>
Styling conventions: [`PEP 8`][pep8] and [`isort`][isort]

## [Release Notes][release-notes]
**Requirement**
```shell
python -m pip install gitverse
```

**Usage**
```shell
gitverse-release reverse -f release_notes.rst -t 'Release Notes'
```

## Linting
`pre-commit` will ensure linting, run pytest, generate runbook & release notes, and validate hyperlinks in ALL
markdown files (including Wiki pages)

**Requirement**
```shell
python -m pip install sphinx==5.1.1 pre-commit recommonmark
```

**Usage**
```shell
pre-commit run --all-files
```

## Pypi Package
[![pypi-module](https://img.shields.io/badge/Software%20Repository-pypi-1f425f.svg)][pypi-repo]

[https://pypi.org/project/jarvis-ironman/][pypi]

## Runbook
[![made-with-sphinx-doc](https://img.shields.io/badge/Code%20Docs-Sphinx-1f425f.svg)][sphinx]

[https://jarvis-docs.vigneshrao.com/][runbook]

## License & copyright

&copy; Vignesh Rao

Licensed under the [MIT License][license]

[python]: https://python.org
[3.10]: https://docs.python.org/3/whatsnew/3.10.html
[3.11]: https://docs.python.org/3/whatsnew/3.11.html
[virtual environment]: https://docs.python.org/3/tutorial/venv.html
[PyCharm]: https://www.jetbrains.com/pycharm/
[VSCode]: https://code.visualstudio.com/download
[repo]: https://api.github.com/repos/thevickypedia/Jarvis
[license]: https://github.com/thevickypedia/Jarvis/blob/master/LICENSE
[pypi]: https://pypi.org/project/jarvis-ironman
[pypi-files]: https://pypi.org/project/jarvis-ironman/#files
[pypi-repo]: https://packaging.python.org/tutorials/packaging-projects/
[wiki]: https://github.com/thevickypedia/Jarvis/wiki
[release-notes]: https://github.com/thevickypedia/Jarvis/blob/master/release_notes.rst
[gha_pages]: https://github.com/thevickypedia/Jarvis/actions/workflows/pages/pages-build-deployment
[gha_pypi]: https://github.com/thevickypedia/Jarvis/actions/workflows/matrix-publisher.yml
[gha_md_valid]: https://github.com/thevickypedia/Jarvis/actions/workflows/markdown.yml
[gha_release_notes]: https://github.com/thevickypedia/Jarvis/actions/workflows/release_notes.yml
[webpage]: https://vigneshrao.com/
[webpage_contact]: https://vigneshrao.com/contact
[Anaconda]: https://docs.conda.io/projects/conda/en/latest/user-guide/install/
[Miniconda]: https://docs.conda.io/en/latest/miniconda.html#windows-installers
[vcpp]: https://visualstudio.microsoft.com/visual-cpp-build-tools/
[git-cli]: https://git-scm.com/download/win/
[google-docs]: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
[pep8]: https://www.python.org/dev/peps/pep-0008/
[isort]: https://pycqa.github.io/isort/
[sphinx]: https://www.sphinx-doc.org/en/master/man/sphinx-autogen.html
[runbook]: https://jarvis-docs.vigneshrao.com/

<!-- labels -->

[label-python]: https://img.shields.io/badge/Made%20with-Python-blue?style=for-the-badge&logo=Python
[label-pyversion]: https://img.shields.io/badge/python-3.10%20%7C%203.11-orange
[label-pypi-downloads]: https://img.shields.io/pypi/dm/jarvis-ironman
[label-platform]: https://img.shields.io/badge/Platform-Linux|macOS|Windows-1f425f.svg

[label-language-ct]: https://img.shields.io/github/languages/count/thevickypedia/Jarvis
[label-code-coverage]: https://img.shields.io/github/languages/top/thevickypedia/Jarvis

[label-license]: https://img.shields.io/github/license/thevickypedia/Jarvis

[label-stars]: https://img.shields.io/github/stars/thevickypedia/Jarvis
[label-forks]: https://img.shields.io/github/forks/thevickypedia/Jarvis
[label-watchers]: https://img.shields.io/github/watchers/thevickypedia/Jarvis

[label-repo-size]: https://img.shields.io/github/repo-size/thevickypedia/Jarvis
[label-code-size]: https://img.shields.io/github/languages/code-size/thevickypedia/Jarvis
[label-code-line]: http://jarvis.vigneshrao.com/line-count?badge=true
[label-file-count]: http://jarvis.vigneshrao.com/file-count?badge=true

[label-issues-closed]: https://img.shields.io/github/issues-closed-raw/thevickypedia/Jarvis
[label-issues-raw]: https://img.shields.io/github/issues-raw/thevickypedia/Jarvis
[label-pr-closed]: https://img.shields.io/github/issues-pr-closed-raw/thevickypedia/Jarvis
[label-pr-raw]: https://img.shields.io/github/issues-pr-raw/thevickypedia/Jarvis

[label-file-count]: https://tokei.rs/b1/github/thevickypedia/Jarvis?category=files
[label-line-of-code]: https://tokei.rs/b1/github/thevickypedia/Jarvis?category=code

[label-stats-Modules]: https://img.shields.io/github/search/thevickypedia/Jarvis/module
[label-stats-Python]: https://img.shields.io/github/search/thevickypedia/Jarvis/.py
[label-stats-Threads]: https://img.shields.io/github/search/thevickypedia/Jarvis/thread
[label-stats-Listener]: https://img.shields.io/github/search/thevickypedia/Jarvis/listener
[label-stats-Speaker]: https://img.shields.io/github/search/thevickypedia/Jarvis/speaker
[label-stats-Bash]: https://img.shields.io/github/search/thevickypedia/Jarvis/.sh
[label-stats-AppleScript]: https://img.shields.io/github/search/thevickypedia/Jarvis/.scpt
[label-stats-Make]: https://img.shields.io/github/search/thevickypedia/Jarvis/Makefile

[label-actions-pages]: https://github.com/thevickypedia/Jarvis/actions/workflows/pages/pages-build-deployment/badge.svg
[label-actions-pypi]: https://github.com/thevickypedia/Jarvis/actions/workflows/matrix-publisher.yml/badge.svg
[label-actions-markdown]: https://github.com/thevickypedia/Jarvis/actions/workflows/markdown.yml/badge.svg
[label-actions-release]: https://github.com/thevickypedia/Jarvis/actions/workflows/release_notes.yml/badge.svg?branch=master

[label-pypi]: https://img.shields.io/pypi/v/jarvis-ironman
[label-pypi-format]: https://img.shields.io/pypi/format/jarvis-ironman
[label-pypi-status]: https://img.shields.io/pypi/status/jarvis-ironman

[label-github-repo-created]: https://img.shields.io/date/1599432310
[label-github-commit-activity]: https://img.shields.io/github/commit-activity/y/thevickypedia/Jarvis
[label-github-last-commit]: https://img.shields.io/github/last-commit/thevickypedia/Jarvis
[label-github-last-release]: https://img.shields.io/github/release-date/thevickypedia/Jarvis

[label-active-development]: https://img.shields.io/badge/Development%20Level-Actively%20Developed-success.svg
[label-actively-maintained]: https://img.shields.io/badge/Maintenance%20Level-Actively%20Maintained-success.svg
[label-maintainer]: https://img.shields.io/badge/Maintained%20By-Vignesh%20Rao-blue.svg

[label-askme]: https://img.shields.io/badge/SELECT%20*%20FROM-questions-1abc9c.svg

[label-open-ssf]: https://api.securityscorecards.dev/projects/github.com/thevickypedia/Jarvis/badge
[link-open-ssf]: https://securityscorecards.dev/viewer/?uri=github.com/thevickypedia/Jarvis
