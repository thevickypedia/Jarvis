#!/bin/sh

os_independent_packages() {
      # Upgrades pip module
    python -m pip install --upgrade pip

    # Installs non version specific packages using --upgrade and --no-cache flag
    python -m pip install --no-cache --upgrade setuptools gmail-connector vpn-server changelog-generator sphinx pre-commit recommonmark

    # Install pre-commit checker to restrict commit if any step in .pre-commit-config.yaml fails.
    pre-commit install

    # Get to the current directory and install the module specific packages from requirements.txt
    current_dir="$(dirname "$(realpath "$0")")"
    python -m pip install --no-cache-dir -r $current_dir/requirements.txt
}

OSName=$(UNAME)

if [[ "$OSName" == "Darwin" ]]; then
    # Checks current version and throws a warning if older han 10.14
    base_ver="10.14"
    ver=$(sw_vers | grep ProductVersion | cut -d':' -f2 | tr -d ' ')
    if awk "BEGIN {exit !($base_ver > $ver)}"; then
        echo -e '\n***************************************************************************************************'
        echo "** You're running MacOS ${ver#"${ver%%[![:space:]]*}"}. Wake word library will not be supported in MacOS older than ${base_ver}. **"
        echo "** This means the audio listened, is converted into text and then condition checked to initiate. **"
        echo -e '***************************************************************************************************\n'
        sleep 3
    fi

    # Looks for brew installation and installs only if brew is not found in /usr/local/bin
    brew_check=$(which brew)
    brew_condition="/usr/local/bin/brew"
    if [[ "$brew_check" != "$brew_condition" ]]; then
        echo "Installing Homebrew"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
        else echo "Found Homebrew, skipping installation"
    fi

    # Looks for git and installs only if git is not found in /usr/bin or /usr/local/bin (if installed using brew)
    git_check=$(which git)
    git_condition_1="/usr/bin/git"
    git_condition_2="/usr/local/bin/git"
    if [[ "$git_check" == "$git_condition_1" || "$git_check" == "$git_condition_2" ]]; then
        echo "Found Git CLI, skipping installation"
        else echo "Installing Git CLI"
        brew install git
    fi

    # Packages installed using homebrew
    brew install portaudio coreutils
    git clone https://github.com/toy/blueutil.git && cd blueutil && make && make install && cd ../ && rm -rf blueutil

    # Installs the OS independent packages
    os_independent_packages

    # Mac specifics
    python -m pip install python-crontab==2.6.0 PyAudio==0.2.11 playsound==1.3.0

    # Install face-recognition/detection dependencies as stand alone so users aren't blocked until then
    python -m pip install opencv-python==4.4.0.44
    python -m pip install cmake==3.18.2.post1
    python -m pip install dlib==19.21.0
    python -m pip install face-recognition==1.3.0
elif [[ "$OSName" == MSYS* ]]; then
    clear
    echo "*****************************************************************************************************************"
    echo "*****************************************************************************************************************"
    echo ""
    echo "Make sure Anaconda (or Miniconda) and VS C++ BuildTools are installed."
    echo ""
    echo "Refer the below links for:"
    echo "Anaconda installation: https://docs.conda.io/projects/conda/en/latest/user-guide/install/"
    echo "Miniconda installation: https://docs.conda.io/en/latest/miniconda.html#windows-installers"
    echo "VisualStudio C++ BuildTools: https://visualstudio.microsoft.com/visual-cpp-build-tools/"
    echo ""
    echo "*****************************************************************************************************************"
    echo "*****************************************************************************************************************"
    read -p "Are you sure you want to continue? <Y/N> " prompt
    if ! [[ $prompt =~ [yY](es)* ]]; then
        echo ""
        echo "***************************************************************************************************************"
        echo "Bye. Hope to see you soon."
        echo "***************************************************************************************************************"
        exit
    fi
    conda install portaudio=19.6.0

    # Upgrades pip module
    python -m pip install --upgrade pip

    # Install pipwin and pyaudio
    pip install pipwin
    pipwin install pyaudio

    pip install git+https://github.com/bisoncorps/search-engine-parser

    # Installs the OS independent packages
    os_independent_packages

    # Install Windows specifics
    python -m pip install pywin32==300 playsound==1.2.2

    # Downloads SetVol.exe fto control volume on Windows
    curl https://thevickypedia.com/Jarvis/SetVol.exe --output SetVol.exe --silent

    # Install face-recognition/detection dependencies as stand alone so users aren't blocked until then
    python -m pip install opencv-python==4.5.5.64
    python -m pip install cmake==3.18.2.post1
    python -m pip install dlib==19.21.0
    python -m pip install face-recognition==1.3.0
else
    clear
    echo "*****************************************************************************************************************"
    echo "*****************************************************************************************************************"
    echo ""
    echo "Current Operating System: $OSName"
    echo "Jarvis is currently supported only on Mac and Windows"
    echo ""
    echo "*****************************************************************************************************************"
    echo "*****************************************************************************************************************"
fi
