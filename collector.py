# -*- coding: utf-8 -*-
"""The main core is Collector"""
import os
from config import Config
from plugins.boardgamegeek import PluginBoardGameGeek
from plugin import PluginManager


class Collector(object):
    """Collector joins all the engine system to load correctly"""

    _instance = None

    # Settings description
    param_definition = {
        'build_user_dir': "Build the user data directory",
        'plugins_enabled': "List of plugins enabled",
    }

    # Default settings
    _settings = {
        'build_user_dir': True,
        'plugins_enabled': ['PluginHellouser', 'PluginBoardGameGeek']
    }

    managers = {}

    """Collector joins everything"""
    def __init__(self, params=None):
        if Collector._instance is not None:
            raise Exception("Called more than once")
        #else
        super(Collector, self).__init__()
        # Parse all the parameters
        self.parse_params(params)
        # Boot the system
        self.boot()

    @staticmethod
    def get_instance(params=None):
        """ Returns the collector instance"""
        if Collector._instance is None:
            Collector._instance = Collector(params)
        return Collector._instance

    def parse_params(self, params):
        """Loads the parameters overriding the defaults"""
        if params is None:
            return
        if not isinstance(params, dict):
            raise ValueError("Params must be a dict")
        for defined in self.param_definition.keys():
            if defined in params:
                self._settings[defined] = params[defined]

    def conf(self, key):
        """Returns the setting value for the requested key"""
        return self._settings[key]

    def boot(self):
        """The boot process of collector"""
        # Configuration
        config = Config.get_instance()
        if self.conf('build_user_dir'):
            config.build_data_directory()
        self.register_manager('config', config)

        # Plug-ins
        sys_plugin_path = config.get_appdata_path()
        sys_plugin_path = os.path.join(sys_plugin_path, 'user_plugins')

        # System plug-ins
        plugins = [PluginBoardGameGeek()]
        sys_plugins = {plugin.get_id(): plugin for plugin in plugins}
        plugin_manager = PluginManager.get_instance(
            self.conf('plugins_enabled'),
            sys_plugins,
            paths=[sys_plugin_path])
        self.register_manager('plugin', plugin_manager)

    def register_manager(self, key, manager):
        """Registers a new manager"""
        self.managers[key] = manager

    def get_manager(self, key):
        """Gets a previously registered manager"""
        return self.managers[key]

    def discover(self, term, plugin_id, provider=None):
        """Search for files that match the term using plugins"""
        plugin = self.managers['plugin'].get(plugin_id)
        return plugin.search(term, provider)

    def get_plugin_file(self, file_id, plugin_id, provider=None):
        """Returns a file provided by a plugin"""
        plugin = self.managers['plugin'].get(plugin_id)
        return plugin.get(file_id, provider)


if __name__ == '__main__':
    Collector()
