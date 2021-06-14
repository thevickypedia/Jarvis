"""This is a basic query to start Jarvis after 5 seconds triggered by the restart() function in main module."""
from os import system
from time import sleep

sleep(5)
system('python3 jarvis.py')
