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


class Config(object):
    """Config allows consult the application paths and other settings"""

    def __init__(self):
        """ Constructor for Config, initialize all the attributes"""
        self.config_dir = None
        self.__file__ = FILEPATH
        self.create_config_directory()
        self.resources = self.get_resources_path()
        #os.read(os.path.join(self.path, 'resources/config/ui.json'))

    def get_resources_path(self):
        """Returns the resources path, in MacOs is the folder Resources
         inside the bundle """
        # determine if application is a script file or frozen exe
        application_path = ''
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable).replace('MacOS',
                 'Resources')
        else:
            application_path = self.__file__.replace('engine', '')
        return application_path

    def get_appdata_path(self):
        """ Returns the app data folder """
        # if isosx:
        #     datapath = datapath.replace('MacOS', 'Resources')
        return os.path.join(self.resources, 'data')

    def create_config_directory(self):
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
                os.makedirs(config_dir, mode=CONFIG_DIR_MODE)
            except:
                pass
        plugin_dir = os.path.join(config_dir, 'plugins')

        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir, mode=CONFIG_DIR_MODE)
        self.config_dir = config_dir

if __name__ == '__main__':
    CONFIG = Config()
