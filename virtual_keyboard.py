from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemanddock')

from kivy.base import runTouchApp
from kivy.lang import Builder

runTouchApp(Builder.load_string('TextInput:'))