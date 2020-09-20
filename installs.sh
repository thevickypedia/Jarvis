/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
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
python3 -m pip install ChatterBot==1.0.0
python3 -m pip install chatterbot-corpus==1.2.0
echo "*** Checking your chrome version to install chromedriver ***"
chrome_v=$(/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version)
echo $chrome_v
raw_v=$(echo $chrome_v | grep -Eo '[0-9]+([.][0-9]+)' | tr '\n' ' '; echo "")
big_v=${raw_v%.*}
v=$(echo $big_v | tr ' ' '.';)
python3 -m pip install chromedriver-py==$v.*