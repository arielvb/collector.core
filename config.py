# -*- coding: utf-8 -*-
"""
Config Class
"""

import os
import sys

CONFIG_DIR_MODE = 0700
PLAT = sys.platform.lower()

ISWINDOWS = 'win32' in PLAT or 'win64' in PLAT
ISOSX = 'darwin' in PLAT

FILEPATH = os.path.dirname(__file__)


def rebuild_constants():
    global CONFIG_DIR_MODE, PLAT, ISWINDOWS, ISOSX, FILEPATH
    CONFIG_DIR_MODE = 0700
    PLAT = sys.platform.lower()

    ISWINDOWS = 'win32' in PLAT or 'win64' in PLAT
    ISOSX = 'darwin' in PLAT

    FILEPATH = os.path.dirname(__file__)

_config_instance = None


class Config(object):
    """Config allows consult the application paths and other settings"""

    def __init__(self, create_directory=False):
        """ Constructor for Config, initialize all the attributes"""
        global _config_instance
        if not _config_instance is None:
            raise Exception("Called more that once")
        self.config_dir = None
        self.__file__ = FILEPATH
        self.create_config_directory(create_directory)
        self.resources = self.get_resources_path()
        _config_instance = self
        #os.read(os.path.join(self.path, 'resources/config/ui.json'))

    @staticmethod
    def getInstance(create_directory=False):
        global _config_instance
        if _config_instance is None:
            _config_instance = Config(create_directory)
        return _config_instance

    def get_resources_path(self):
        """Returns the resources path, in MacOs is the folder Resources
         inside the bundle """
        # determine if application is a script file or frozen exe
        application_path = ''
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
            if ISOSX:
                application_path = application_path.replace('MacOS',
                 'Resources')
        else:
            application_path = self.__file__.replace('engine', '')
        return os.path.abspath(application_path)

    def get_appdata_path(self):
        """ Returns the app data folder """
        return os.path.join(self.resources, 'data')

    def create_config_directory(self, create):
        """ Creates the config directory inside the user folder,
         the exact location depends of the OS"""
        config_dir = None
        if ISWINDOWS:
            # TODO try to use distutils get_special_folder_path
            #config_dir = get_special_folder_path("CSIDL_APPDATA")
            config_dir = os.path.expanduser('~')
            config_dir = os.path.join(config_dir, 'Collector')
        elif ISOSX:
            config_dir = os.path.expanduser(
                    '~/Library/Application Support/Collector')
        else:
            bdir = os.path.abspath(os.path.expanduser(
                    os.environ.get('XDG_CONFIG_HOME', '~/.config')))
            config_dir = os.path.join(bdir, 'collector')
            try:
                if create:
                    os.makedirs(config_dir, mode=CONFIG_DIR_MODE)
            except:
                pass
        plugin_dir = os.path.join(config_dir, 'plugins')

        if not os.path.exists(plugin_dir) and create:
            os.makedirs(plugin_dir, mode=CONFIG_DIR_MODE)
        self.config_dir = config_dir
