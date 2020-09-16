echo "**********************************************************************************************************"
echo "Install Anaconda and make sure 'pip3' command works before proceeding."
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