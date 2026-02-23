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
