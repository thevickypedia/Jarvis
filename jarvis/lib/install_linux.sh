#!/bin/bash
# 'set -e' stops the execution of a script if a command or pipeline has an error.
# This is the opposite of the default shell behaviour, which is to ignore errors in scripts.
set -e

if ! [ -x "$(command -v python)" ]; then
  alias python=python3
fi

sudo apt update
dot_ver=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
sudo apt install -y "python$dot_ver-distutils" # Install distutils for the current python version
sudo apt-get install -y git libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0
sudo apt install -y build-essential ffmpeg espeak python3-pyaudio "python$dot_ver-dev"

sudo apt install -y libopencv-dev python3-opencv

sudo apt install -y python3-gi
sudo apt install -y pkg-config libcairo2-dev gcc python3-dev libgirepository1.0-dev

sudo apt install -y gnome-screensaver brightnessctl v4l-utils

# Install Linux specifics
${PY_EXECUTABLE} pip install pvporcupine==1.9.5

# CMake must be installed to build dlib
python -m pip uninstall --no-cache-dir cmake # Remove cmake distro installed by pip
sudo apt install cmake                       # Install cmake from apt repository
# shellcheck disable=SC2154
if [ "$pyversion" -eq 310 ]; then
  ${PY_EXECUTABLE} pip install dlib==19.24.0
fi
if [ "$pyversion" -eq 311 ]; then
  ${PY_EXECUTABLE} pip install dlib==19.24.4
fi

# Install as stand alone as face recognition depends on dlib
${PY_EXECUTABLE} pip install opencv-python==4.9.0.80 face-recognition==1.3.0

${PY_EXECUTABLE} pip install gobject==0.1.0 PyGObject==3.48.2

# Install as stand alone as playsound depends on gobject
${PY_EXECUTABLE} pip install playsound==1.3.0
