"""This is a basic query to start Jarvis after 5 seconds triggered by the restart() in jarvis.py"""
from os import system
from time import sleep

sleep(5)
system('python3 jarvis.py')
