"""This is a basic query to start Jarvis after 5 seconds triggered by the restart() in jarvis.py"""
import os
import time

time.sleep(5)
os.system('python3 jarvis.py')
