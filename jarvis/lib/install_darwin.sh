#!/bin/bash
# 'set -e' stops the execution of a script if a command or pipeline has an error.
# This is the opposite of the default shell behaviour, which is to ignore errors in scripts.
set -e

if ! [ -x "$(command -v python)" ]; then
  alias python=python3
fi

# Looks for xcode installation and installs only if xcode is not found already
which xcodebuild >tmp_xcode && xcode_check=$(cat tmp_xcode) && rm tmp_xcode
if [[ "$xcode_check" == "/usr/bin/xcodebuild" ]] || [[ $HOST == "/*" ]]; then
  xcode_version=$(pkgutil --pkg-info=com.apple.pkg.CLTools_Executables | grep version)
  echo "xcode $xcode_version"
else
  echo "Installing xcode"
  xcode-select --install
fi

# Looks for brew installation and installs only if brew is not found
if ! [ -x "$(command -v brew)" ]; then
  echo "Installing Homebrew"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
fi
brew -v >tmp_brew && brew_version=$(head -n 1 tmp_brew) && rm tmp_brew
echo "$brew_version"

# Disable brew auto update, cleanup and env hints
export HOMEBREW_NO_ENV_HINTS=1
export HOMEBREW_NO_AUTO_UPDATE=1
export HOMEBREW_NO_INSTALL_CLEANUP=1

# Looks for git and installs only if git is not found in /usr/bin or /usr/local/bin (if installed using brew)
if ! [ -x "$(command -v git)" ]; then
  echo "Installing Git CLI"
  brew install git
fi
git_version="$(git --version)"
echo "$git_version"

# Packages installed using homebrew
brew install portaudio coreutils ffmpeg lame

# Install macOS specifics
${PY_EXECUTABLE} pip install playsound==1.3.0 ftransc==7.0.3 pyobjc-framework-CoreWLAN==9.0.1

# Uninstall any remaining cmake packages from pypi before brew installing it to avoid conflict
python -m pip uninstall --no-cache --no-cache-dir cmake && brew install cmake

# shellcheck disable=SC2154
if [ "$pyversion" -eq 310 ]; then
  ${PY_EXECUTABLE} pip install dlib==19.24.0
fi
if [ "$pyversion" -eq 311 ]; then
  ${PY_EXECUTABLE} pip install dlib==19.24.4
fi
${PY_EXECUTABLE} pip install opencv-python==4.9.0.80

# shellcheck disable=SC2154
if [[ "$architecture" == "arm64" ]]; then
  ${PY_EXECUTABLE} pip install pvporcupine==3.0.2
else
  ${PY_EXECUTABLE} pip install pvporcupine==1.9.5
fi

# Install as stand alone as face recognition depends on dlib
${PY_EXECUTABLE} pip install face-recognition==1.3.0
