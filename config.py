# -*- coding: utf-8 -*-
# pylint: disable-msg=W0603
# W0603: Using the global statement
"""
Configuration
-------------

This module calculates/recover the settings of Collector.
"""

import os
import sys

PLAT = sys.platform.lower()

ISWINDOWS = 'win32' in PLAT or 'win64' in PLAT
ISOSX = 'darwin' in PLAT

FILEPATH = os.path.dirname(__file__)


def rebuild_constants():
    """Returns constants to the default value"""
    global PLAT, ISWINDOWS, ISOSX, FILEPATH
    PLAT = sys.platform.lower()

    ISWINDOWS = 'win32' in PLAT or 'win64' in PLAT
    ISOSX = 'darwin' in PLAT

    FILEPATH = os.path.dirname(__file__)


class Config(object):
    """Config is the main class for this module; initialize the values with
     the default configuration, allows query/edit or save it's state."""

    _instance = None
    OSX = 1
    WINDOWS = 2
    OTHER = 3
    DIR_MODE = 0700

    # Settings description
    param_definition = {
        'build_user_dir': "Build the user data directory",
        'plugins_enabled': "List of plugins enabled",
        'home': "The application data directory, could be a path or:" +
                " ':auto:', ':resources:'",
        'lang': """The application language must be locale_COUNTRY
                    or ':system:'.
                    Examples:
                        en_UK for English (United Kingdom)
                        ca_ES for catalan
                        es_ES for spanish
                """,
    }

    # Default settings
    _default = {
        'build_user_dir': True,
        'plugins_enabled': [],
        'home': ':auto:',
        'lang': ':system:',
    }

    def __init__(self, platform=None):
        """ Constructor for Config, initialize all the attributes"""
        if not Config._instance is None:
            raise Exception("Called more that once")
        self.__file__ = FILEPATH
        if platform is None:
            platform = Config.get_current_os()
        elif platform not in [Config.OSX, Config.WINDOWS, Config.OTHER]:
            raise Exception("Platform identifier %s not found" % platform)
        self.platform = platform
        self.resources = self.get_resources_path()
        #self.config_dir = Config.calculate_data_path(platform)
        #self.config_dir = self.get_appdata_path()  # TODO remove me!
        # Parse all the parameters
        self._settings = []
        self.set_settings(None)

        #os.read(os.path.join(self.path, 'resources/config/ui.json'))

    def set_settings(self, params):
        """Loads the parameters overriding the defaults"""
        # import ipdb; ipdb.set_trace( )
        settings = self._default.copy()
        if params is not None:
            if not isinstance(params, dict):
                raise ValueError("Params must be a dict")
            for defined in self.param_definition.keys():
                if defined in params:
                    settings[defined] = params[defined]
        self._settings = self.translate_values(settings)

    def translate_values(self, settings):
        """Translates special values to the real values"""
        if settings['home'] == ':auto:':
            settings['home'] = Config.calculate_data_path(self.platform)
        elif settings['home'] == ':resources:':
            settings['home'] = self.get_appdata_path()
        return settings

    @staticmethod
    def get_instance():
        """Returns the config instance"""
        if Config._instance is None:
            Config._instance = Config()
        return Config._instance

    def get_resources_path(self):
        """Returns the resources path, in MacOs is the folder Resources
         inside the bundle """
        # determine if application is a script file or frozen exe
        application_path = ''
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
            if self.platform == Config.OSX:
                application_path = application_path.replace('MacOS',
                 'Resources')
        else:
            application_path = self.__file__.replace('engine', '')
        return os.path.abspath(application_path)

    def get_appdata_path(self):
        """Returns the app data folder, this folder is inside the
         application"""
        return os.path.join(self.resources, 'data')

    def get_data_path(self):
        """Returns the user data path (home)"""
        return self._settings['home']

    get_home = get_data_path

    def get_plugin_path(self):
        """Returns the user plugin path"""
        return os.path.join(self._settings['home'], 'plugins')

    @staticmethod
    def get_current_os(platform=None):
        """Try to discover the current OS"""
        if platform is None:
            platform = sys.platform
        platform = platform.lower()
        if platform in 'win32' or platform in 'win64':
            return Config.WINDOWS
        elif platform in 'darwin':
            return Config.OSX
        else:
            return Config.OTHER

    @staticmethod
    def calculate_data_path(platform=None):
        """ Calculates the user data directory,
         the exact location depends of the OS"""
        config_dir = None
        if platform is None:
            platform = Config.get_current_os()
        if platform == Config.WINDOWS:
            # TODO try to use distutils get_special_folder_path
            #config_dir = get_special_folder_path("CSIDL_APPDATA")
            config_dir = os.path.expanduser('~')
            config_dir = os.path.join(config_dir, 'Collector')
        elif platform == Config.OSX:
            config_dir = os.path.expanduser(
                    '~/Library/Application Support/Collector')
        else:
            bdir = os.path.abspath(os.path.expanduser(
                    os.environ.get('XDG_CONFIG_HOME', '~/.config')))
            config_dir = os.path.join(bdir, 'collector')
        return config_dir

    def build_data_directory(self):
        """Creates the content inside the user data directory"""
        subfolders = ['user_plugins', 'config', 'collections']
        import shutil
        base = self._settings['home']
        if not os.path.exists(base):
            os.makedirs(base, mode=Config.DIR_MODE)
            appdata = self.get_appdata_path()
            # Do a full copy because no previus data exists
            for folder in subfolders:
                dst = os.path.join(base, folder)
                src = os.path.join(appdata, folder)
                shutil.copytree(src, dst)
        # TODO check if some data is missing?

    def conf(self, key):
        """Returns the setting value for the requested key"""
        return self._settings[key]

