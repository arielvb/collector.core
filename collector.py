# -*- coding: utf-8 -*-
"""The main core is Collector"""
import os
from config import Config
from plugins.boardgamegeek import PluginBoardGameGeek
from plugin import PluginManager
from collection import CollectionManager


class Collector(object):
    """Collector joins all the engine system to load correctly"""

    _instance = None

    managers = {}

    def __init__(self, home=None):
        if Collector._instance is not None:
            raise Exception("Called more than once")
        #else
        super(Collector, self).__init__()
        # Configuration
        config = Config.get_instance()
        self.register_manager('config', config)
        if home is not None:
            config.set_home(home)

        if self.conf('build_user_dir'):
            config.build_data_directory()

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
        self.register_manager('collection',
             CollectionManager.get_instance(True))

    @staticmethod
    def get_instance(params=None):
        """ Returns the collector instance"""
        if Collector._instance is None:
            Collector._instance = Collector(params)
        return Collector._instance

    def conf(self, key):
        """Returns the setting value for the requested key, this is a proxy
        method to the manager Config"""
        return self.managers['config'].conf(key)

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

    def quick_search(self, term, collection):
        """Returns the results of the quick search for term in
         the selected collection"""
        man = self.managers['collection'].get_collection(collection)
        return man.query(term)


if __name__ == '__main__':
    Collector()
