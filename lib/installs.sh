# looks for brew installation and installs only if brew is not found in /usr/local/bin
brew_check=$(which brew)
brew_condition="/usr/local/bin/brew"
if [[ "$brew_check" != "$brew_condition" ]]; then
  echo "Installing Homebrew"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
  else echo "Found Homebrew, skipping installation"
fi
# looks for git installation and installs only if git is not found in /usr/bin
git_check=$(which git)
git_condition="/usr/bin/git"
if [[ "$git_check" != "$git_condition" ]]; then
  echo "Installing Git CLI"
  brew install git
  else echo "Found Git CLI, skipping installation"
fi
#python3 -m venv venv
brew install portaudio
git clone https://github.com/toy/blueutil.git && cd blueutil && make && make install && cd ../ && rm -rf blueutil
pip install --upgrade pip
python3 -m pip install SpeechRecognition==3.8.1
python3 -m pip install PyAudio==0.2.11
python3 -m pip install pyttsx3==2.90
python3 -m pip install pytemperature==1.0
python3 -m pip install psutil==5.7.2
python3 -m pip install wikipedia==1.4.0
python3 -m pip install newsapi-python==0.2.6
python3 -m pip install pyrh==2.0
python3 -m pip install pytz==2020.1
python3 -m pip install pyicloud==0.9.7
python3 -m pip install geopy==2.0.0
python3 -m pip install PyDictionary==2.0.1
python3 -m pip install ChatterBot==1.0.0
python3 -m pip install chatterbot-corpus==1.2.0
python3 -m pip install googlehomepush==0.1.0
python3 -m pip3 install randfacts==0.2.6
python3 -m pip3 install PyAutoGui==0.9.52
python3 -m pip3 install wikiquotes==1.4
python3 -m pip install axju-jokes==1.0.3
python3 -m pip install timezonefinder==4.4.1
python3 -m pip install inflect==4.1.0
python3 -m pip install wordninja==2.0.0
python3 -m pip install search_engine_parser==0.6.2
python3 -m pip install boto3==1.16.12
python3 -m pip install playsound==1.2.2
python3 -m pip install pywebostv==0.8.4
python3 -m pip install wakeonlan==1.1.6
python3 -m pip install opencv-python==4.4.0.44
python3 -m pip install cmake==3.18.2.post1
python3 -m pip install dlib==19.21.0
python3 -m pip install face-recognition==1.3.0
python3 -m pip install speedtest-cli==2.1.2
python3 -m pip install holidays==0.10.4
