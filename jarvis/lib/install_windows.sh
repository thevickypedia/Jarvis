#!/bin/bash
# 'set -e' stops the execution of a script if a command or pipeline has an error.
# This is the opposite of the default shell behaviour, which is to ignore errors in scripts.
set -e

if ! [ -x "$(command -v python)" ]; then
  alias python=python3
fi

git_version="$(conda --version)"
echo "$git_version"

git_version="$(git --version)"
echo "$git_version"

conda install ffmpeg=4.2.2 portaudio=19.6.0

# Install Windows specifics
${PY_EXECUTABLE} pip install pywin32==305 playsound==1.2.2 pydub==0.25.1 pvporcupine==1.9.5

# CMake must be installed to build dlib
python -m pip uninstall --no-cache-dir cmake # Remove cmake distro installed by pip
conda install cmake                          # Install cmake from conda
# shellcheck disable=SC2154
if [ "$pyversion" -eq 310 ]; then
  ${PY_EXECUTABLE} pip install dlib==19.24.0
fi
if [ "$pyversion" -eq 311 ]; then
  ${PY_EXECUTABLE} pip install dlib==19.24.4
fi

# Install as stand alone as face recognition depends on dlib
${PY_EXECUTABLE} pip install opencv-python==4.9.0.80 face-recognition==1.3.0
