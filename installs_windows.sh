echo "**********************************************************************************************************"
echo "Install Anaconda and make sure 'pip3' command works before proceeding."
echo "Refer this link for pip3 installation guide: https://stackoverflow.com/questions/41501636/how-to-install-pip3-on-windows"
echo "**********************************************************************************************************"
echo "Starting conda installations"
conda install portaudio
conda install SpeechRecognition
conda install PyAudio
echo "Starting pip3 installations"
pip3 install numpy
pip3 install pyttsx3
pip3 install SpeechRecognition
pip3 install pytemperature
pip3 install psutil
pip3 install wikipedia
pip3 install newsapi-python
pip3 install pyrh
pip3 install pytz
pip3 install ChatterBot==1.0.0 --ignore-installed PyYAML
pip3 install chatterbot-corpus==1.2.0 --ignore-installed PyYAML
pip3 install sqlalchemy==1.2
#pip3 install python-dateutil==2.7