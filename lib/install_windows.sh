clear
echo "*****************************************************************************************************************"
echo "*****************************************************************************************************************"
echo ""
echo "Make sure Anaconda (or Miniconda) and VS C++ BuildTools are installed."
echo "The commands 'conda' and 'pip3' should be operational before proceeding."
echo ""
echo "Refer the below links for:"
echo "Anaconda installation: https://docs.conda.io/projects/conda/en/latest/user-guide/install/"
echo "Miniconda installation: https://docs.conda.io/en/latest/miniconda.html#windows-installers"
echo "pip3 setup guide: https://stackoverflow.com/questions/41501636/how-to-install-pip3-on-windows"
echo "VisualStudio C++ BuildTools: https://visualstudio.microsoft.com/visual-cpp-build-tools/"
echo ""
echo "*****************************************************************************************************************"
echo "*****************************************************************************************************************"
read -p "Are you sure you want to continue? <Y/N> " prompt
if ! [[ $prompt =~ [yY](es)* ]]
then
  echo ""
  echo "***************************************************************************************************************"
  echo "Bye. Hope to see you soon."
  echo "***************************************************************************************************************"
  exit
fi

conda install portaudio=19.6.0
pip install pipwin
pipwin install pyaudio
pip install git+https://github.com/bisoncorps/search-engine-parser

# Upgrades pip module
python3 -m pip install --upgrade pip

# Installs non version specific packages using --upgrade and --no-cache flag
python3 -m pip install --no-cache --upgrade setuptools gmail-connector vpn-server changelog-generator sphinx pre-commit recommonmark

# Install pre-commit checker to restrict commit if any step in .pre-commit-config.yaml fails.
pre-commit install

# Get to the current directory and install the module specific packages from requirements.txt
current_dir="$(dirname "$(realpath "$0")")"
python3 -m pip install --no-cache-dir -r $current_dir/win_requirements.txt

# Install face-recognition/detection dependencies as stand alone so users aren't blocked until then
python3 -m pip install opencv-python==4.5.5.64
python3 -m pip install cmake==3.18.2.post1
python3 -m pip install dlib==19.21.0
python3 -m pip install face-recognition==1.3.0
