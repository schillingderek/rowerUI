from gpiozero import Button
from signal import pause
from db_connector import DbConnector

def say_goodbye(self):
	DbConnector.record_wheel_rotation(self)

button = Button(2)

button.when_released = say_goodbye

pause()
