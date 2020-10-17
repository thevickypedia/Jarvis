# looks for brew installation and installs only if brew is not found in /usr/local/bin
check=$(which brew)
condition="/usr/local/bin/brew"
if [[ "$check" != "$condition" ]]; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
  echo "Installing Homebrew"
  else echo "Found Homebrew, skipping installation"
fi
#python3 -m venv venv
brew install portaudio
pip install --upgrade pip
python3 -m pip install SpeechRecognition
python3 -m pip install PyAudio
python3 -m pip install numpy
python3 -m pip install pyttsx3
python3 -m pip install pytemperature
python3 -m pip install psutil
python3 -m pip install wikipedia
python3 -m pip install newsapi-python
python3 -m pip install pyrh
python3 -m pip install pytz
python3 -m pip install pyicloud
python3 -m pip install geopy
python3 -m pip install PyDictionary
python3 -m pip install ChatterBot==1.0.0
python3 -m pip install chatterbot-corpus==1.2.0
python3 -m pip install haversine
python3 -m pip install googlehomepush
python3 -m pip install axju-jokes