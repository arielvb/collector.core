# -*- coding: utf-8 -*-
"""The main core is Collector"""
import os
from config import Config
from plugins.boardgamegeek import PluginBoardGameGeek
from plugin import PluginManager
from collection import Collection
import logging


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
             Collection.get_instance(True))

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
        collection = self.managers['collection'].get_collection(collection)
        return collection.query(term)

    def add(self, data, collection_id, use_mapping):
        """Adds the data to the collection with id *collection_id* and uses the
         selected mapping"""
        man = self.managers['collection']
        mapping = man.get_mapping(use_mapping)
        collection = man.get_collection(collection_id)
        data = self.remap(data, mapping)
        fields = collection.schema.file
        for key in data:
            if key in fields:
                field = fields[key]
                value = data[key]
                if field.class_ == 'ref':
                    ref = man.get_collection(field.ref_collection)
                    refvalue = None
                    if field.is_multivalue():
                        refvalue = []
                        value = self.to_multivalue(value)
                        for i in value:
                            obj = self._get_or_create(ref, field.ref_field, i)
                            refvalue.append(obj.id)
                    else:
                        value = self.to_single(value)
                        # Refvalue must be the id
                        refvalue = self._get_or_create(
                            ref,
                            field.ref_field,
                            value).id
                    data[key] = refvalue
                elif field.is_multivalue():
                    data[key] = self.to_multivalue(value)
                else:
                    data[key] = self.to_single(value)
            else:
                logging.info('Wrong mapper %s for collection %s, not found %s',
                             use_mapping, collection_id, use_mapping)
                del data[key]

        # Create the reduced and remaped data
        collection.save(data)

    @classmethod
    def to_multivalue(cls, data):
        """If data is single transforms it to multivalue"""
        if not isinstance(data, list):
            data = [data]
        return data

    @classmethod
    def to_single(cls, data):
        """If data is multivalue reduces it to a single, if data is a list
        whit more than one element returns the first one"""
        # More complex transformation needs the source schema
        #  float to int,str ; double to int, str; str to int, float
        if isinstance(data, list):
            if len(data) > 0:
                data = data[0]
            else:
                data = None
        return data

    @classmethod
    def _get_or_create(cls, collection, key, value):
        """Looks if exists any entry that matches key==value, if not
         it creates one"""
        exists = collection.filter({'equals': [key, value]})
        if len(exists) == 0:
            return collection.save({key: value})
        else:
            return exists[0]

    @classmethod
    def remap(cls, data, mapping):
        """Returns the data with the new mapping"""
        newdata = {}
        for i in mapping.items():
            if i[0] in data:
                newdata[i[1]] = data[i[0]]
        return newdata

if __name__ == '__main__':
    Collector()
