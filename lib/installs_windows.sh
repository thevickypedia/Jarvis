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
if [[ $prompt =~ [yY](es)* ]]
then
  conda install portaudio=19.6.0
  conda install pyaudio=0.2.11
  pip3 install pyttsx3==2.71
  pip3 install SpeechRecognition==3.8.1
  pip3 install psutil==5.8.0
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
  pip3 install boto3==1.16.12
  pip3 install cmake==3.18.2.post1
  pip3 install dlib==19.21.0
  pip3 install opencv-python=4.5.3.56
  pip3 install face-recognition==1.3.0
  pip3 install playsound==1.2.2
  pip3 install pywebostv==0.8.4
  pip3 install wakeonlan==1.1.6
  pip3 install speedtest-cli==2.1.3
  pip3 install holidays==0.10.4
  pip3 install randfacts==0.2.8
  pip3 install pywin32==300
  pip3 install wolframalpha==4.1.1
  pip3 install pynetgear==0.7.0
  pip3 install gmail-connector  # Don't specify version since I anticipate to make further changes to the module
  pip install git+https://github.com/bisoncorps/search-engine-parser
else
  echo ""
  echo "***************************************************************************************************************"
  echo "Bye. Hope to see you soon."
  echo "***************************************************************************************************************"
fi
