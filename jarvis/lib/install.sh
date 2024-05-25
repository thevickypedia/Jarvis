#!/bin/bash
# 'set -e' stops the execution of a script if a command or pipeline has an error.
# This is the opposite of the default shell behaviour, which is to ignore errors in scripts.
set -e

# defaults
osname=""
architecture=""

# Get to the current directory
current_dir="$(dirname "$(realpath "$0")")"
export current_dir=$current_dir
source "$current_dir/squire/detector.sh"
source "$current_dir/squire/functions.sh"

ver=$(python -c "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')")
echo_ver=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")

# todo: check installation on Windows with 3.11 and remove the wheel file dependency
if [ "$ver" -eq 310 ] || [ "$ver" -eq 311 ]; then
  echo -e '\n***************************************************************************************************'
  echo "                               $osname running python $echo_ver"
  echo -e '***************************************************************************************************\n'
else
  echo "Python version $echo_ver is unsupported for Jarvis. Please use any python version between 3.10.* and 3.11.*"
  exit 1
fi

# Upgrades pip, setuptools and wheel
python -m pip install --upgrade pip setuptools wheel

if [[ "$osname" == "darwin" ]]; then
    echo -e '\n***************************************************************************************************'
    echo "                             Installing dependencies specific to macOS"
    echo -e '***************************************************************************************************\n'

    # Looks for xcode installation and installs only if xcode is not found already
    which xcodebuild > tmp_xcode && xcode_check=$(cat tmp_xcode) && rm tmp_xcode
    if  [[ "$xcode_check" == "/usr/bin/xcodebuild" ]] || [[ $HOST == "/*" ]] ; then
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
    brew -v > tmp_brew && brew_version=$(head -n 1 tmp_brew) && rm tmp_brew
    echo "$brew_version"

		# Looks for git and installs only if git is not found in /usr/bin or /usr/local/bin (if installed using brew)
		if ! [ -x "$(command -v git)" ]; then
			echo "Installing Git CLI"
      brew install git
		fi
		git_version="$(git --version)"
		echo "$git_version"

    # Packages installed using homebrew
    brew install portaudio coreutils ffmpeg lame

    # Installs the OS agnostic packages
    os_agnostic "$current_dir"

    # Mac specifics
    python -m pip install PyAudio==0.2.13 playsound==1.3.0 ftransc==7.0.3 pyobjc-framework-CoreWLAN==9.0.1

    # Checks current version and installs legacy version of dependencies if macOS is older han 10.14
    base_ver="10.14"  # Versions older than Mojave (High Sierra and older versions)
    os_ver=$(sw_vers | grep ProductVersion | cut -d':' -f2 | tr -d ' ')
    # Uninstall any remaining cmake packages from pypi before brew installing it to avoid conflict
    python -m pip uninstall --no-cache --no-cache-dir cmake && brew install cmake
    if awk "BEGIN {exit !($base_ver > $os_ver)}"; then
      # fixme: not sure if this is still valid in new versions of python, no way for the author to test High Sierra
      # todo: print deprecation warning before next major release
      python -m pip install pvporcupine==1.6.0 dlib==19.21.0 opencv-python==4.4.0.44
    else
      if [ "$ver" -eq 310 ]; then
        python -m pip install dlib==19.24.0
      fi
      if [ "$ver" -eq 311 ]; then
        python -m pip install dlib==19.24.4
      fi
      python -m pip install pvporcupine==1.9.5 opencv-python==4.9.0.80
    fi

    # Install as stand alone as face recognition depends on dlib
    python -m pip install face-recognition==1.3.0
elif [[ "$osname" == "windows" ]]; then
    clear
    echo "*****************************************************************************************************************"
    echo "                            Installing dependencies specific to Windows"
    echo "*****************************************************************************************************************"
    echo ""
    echo "Make sure Git, Anaconda (or Miniconda) and VS C++ BuildTools are installed."
    echo ""
    echo "Refer the below links for:"
    echo "Anaconda installation: https://docs.conda.io/projects/conda/en/latest/user-guide/install/"
    echo "Miniconda installation: https://docs.conda.io/en/latest/miniconda.html#windows-installers"
    echo "VisualStudio C++ BuildTools: https://visualstudio.microsoft.com/visual-cpp-build-tools/"
    echo "Git: https://git-scm.com/download/win/"
    echo ""
    echo "*****************************************************************************************************************"
    echo "*****************************************************************************************************************"
    read -r -p "Are you sure you want to continue? <Y/N> " prompt
    if ! [[ $prompt =~ [yY](es)* ]]; then
        echo ""
        echo "***************************************************************************************************************"
        echo "Bye. Hope to see you soon."
        echo "***************************************************************************************************************"
        exit
    fi

    download_from_ext_sources_windows "PyAudio-0.2.11-cp$ver-cp$ver-win_amd64.whl"

    conda install portaudio=19.6.0

    # Installs the OS agnostic packages
    os_agnostic "$current_dir"

    # Install Windows specifics
    python -m pip install pywin32==305 playsound==1.2.2 pydub==0.25.1 pvporcupine==1.9.5

    # Install face-recognition/detection dependencies as stand alone so users aren't blocked until then
    python -m pip install opencv-python==4.5.5.64
    python -m pip install cmake==3.25.0
    python -m pip install dlib==19.24.0
    python -m pip install face-recognition==1.3.0
elif [[ "$osname" == "linux" ]]; then
    echo -e '\n***************************************************************************************************'
    echo "                             Installing dependencies specific to Linux"
    echo -e '***************************************************************************************************\n'

    dot_ver=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    sudo apt install -y "python$dot_ver-distutils"  # Install distutils for the current python version
    sudo apt-get install -y git libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0
    sudo apt install -y build-essential ffmpeg espeak python3-pyaudio "python$dot_ver-dev"

    sudo apt install -y libopencv-dev python3-opencv

    sudo apt install -y python3-gi
    sudo apt install -y pkg-config libcairo2-dev gcc python3-dev libgirepository1.0-dev

    sudo apt install -y gnome-screensaver brightnessctl v4l-utils

    # Installs the OS agnostic packages
    os_agnostic "$current_dir"

    python -m pip install pyaudio pvporcupine==1.9.5 PyAudio==0.2.12

    # CMake must be installed to build dlib
    python -m pip install cmake==3.25.0
    python -m pip install dlib==19.24.0 opencv-python==4.5.5.64

    # Install as stand alone as face recognition depends on dlib
    python -m pip install face-recognition==1.3.0

    python -m pip install gobject PyGObject

    # Install as stand alone as playsound depends on gobject
    python -m pip install playsound==1.3.0
else
    # todo: include support for raspberry-pi
    # todo: possible arch (arm11, cortex-a7, cortex-a53, cortex-53-aarch64, cortex-a72, cortex-a72-aarch64)
    clear
    echo "*****************************************************************************************************************"
    echo "*****************************************************************************************************************"
    echo ""
    echo "Current Operating System: $osname"
    echo "Jarvis is currently supported only on Linux, MacOS and Windows"
    echo ""
    echo "*****************************************************************************************************************"
    echo "*****************************************************************************************************************"
fi

freezer="$osname-$architecture-python$ver.txt"
echo "Freezing the dependencies to $freezer"
python -m pip freeze > "$current_dir/frozen/$freezer"
