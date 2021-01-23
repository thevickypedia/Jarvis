echo "**********************************************************************************************************"
echo "Make sure Anaconda is installed, the commands 'conda' and 'pip3' work before proceeding."
echo ""
echo "Refer the below links for:"
echo "Anaconda installation: https://docs.conda.io/projects/conda/en/latest/user-guide/install/"
echo "pip3 setup guide: https://stackoverflow.com/questions/41501636/how-to-install-pip3-on-windows"
echo "**********************************************************************************************************"
read -p "Are you sure you want to continue? <Y/N> " prompt
if [[ $prompt =~ [yY](es)* ]]
then
  conda install portaudio=19.6.0
  conda install pyaudio=0.2.11
  pip3 install pyttsx3==2.71
  pip3 install SpeechRecognition==3.8.1
  pip3 install pytemperature==1.0
  pip3 install psutil==5.7.2
  pip3 install wikipedia==1.4.0
  pip3 install newsapi-python==0.2.6
  pip3 install pyrh==2.0
  pip3 install pytz==2020.1
  pip3 install pyicloud==0.9.7
  pip3 install geopy==2.0.0
  pip3 install PyDictionary==2.0.1
  pip3 install ChatterBot==1.0.0
  pip3 install chatterbot-corpus==1.2.0
  pip3 install sqlalchemy==1.2
  pip3 install sqlalchemy==1.3.6
  pip3 install googlehomepush==0.1.0
  pip3 install axju-jokes==1.0.3
  pip3 install timezonefinder==4.4.1
  pip3 install inflect==4.1.0
  pip3 install wordninja==2.0.0
  pip3 install search_engine_parser==0.6.2
  pip3 install boto3==1.16.12
  pip3 install playsound==1.2.2
  pip3 install pywebostv==0.8.4
  pip3 install wakeonlan==1.1.6
  pip3 install speedtest-cli==2.1.2
  pip3 install holiday==0.10.4
  pip3 install randfacts==0.2.6
  pip3 install PyAutoGui==0.9.52
  pip3 install wikiquotes==1.4
  
else
  echo ""
  echo "**********************************************************************************************************"
  echo "Bye. Hope to see you soon."
  echo "**********************************************************************************************************"
fi
