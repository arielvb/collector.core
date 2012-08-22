# -*- coding: utf-8 -*-
import os
import sys

from PyQt4.Qt import qDebug
_plat = sys.platform.lower()

iswin = 'win32' in _plat or 'win64' in _plat
isosx = 'darwin' in _plat

filepath = os.path.dirname(__file__)


class Config():

    def __init__(self):
        global isosx, filepath
        self.isosx = isosx
        self.__file__ = filepath
        self.path = self._getPath()
        #os.read(os.path.join(self.path, 'resources/config/ui.json'))

    def _getPath(self):
        # determine if application is a script file or frozen exe
        application_path = ''
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable).replace('MacOS', 'Resources')
        else:
            application_path = self.__file__.replace('engine', '')
        return application_path

    def getDataFolder(self):
        qDebug(self.path)
        # if isosx:
        #     datapath = datapath.replace('MacOS', 'Resources')
        return os.path.join(self.path, 'data')
