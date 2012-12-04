# -*- coding: utf-8 -*-
"""
Collector - Frontcontroller and Helpers
=======================================

The frontcontroller puts together the pieces of the engine, offering a common
 point of access. The frontcontroller, *Collector*, is defined as a singleton
 class, that means you can't create more that one instance.

More over offers shortcuts (methods) to acces to the more common properties,
 one of this shortcuts is *get_manager*
"""
from collection import Collection
from config import Config
from persistence import PersistenceManager
from plugin import PluginManager
import logging
import os


class Collector(object):
    """
    Collector is the frontcontroller to acces to all the pieces of
     collector.engine.
    """

    _instance = None

    managers = {}

    def __init__(self, home=None):
        if Collector._instance is not None:
            raise Exception("Called more than once")
        Collector._instance = self
        super(Collector, self).__init__()
        # Configuration
        config = Config.get_instance()
        self.add_manager('config', config)
        if home is not None:
            config.set_home(home)

        if self.conf('build_user_dir'):
            config.build_data_directory()

        # Plug-ins
        sys_plugin_path = config.get_appdata_path()
        sys_plugin_path = os.path.join(sys_plugin_path, 'user_plugins')

        # System plug-ins
        from collector.plugins import get_sys_plugins
        plugins = get_sys_plugins()
        # Dictionary compression is avaible for >= python 2.7
        sys_plugins = {plugin.get_id(): plugin for plugin in plugins}
        plugin_manager = PluginManager.get_instance(
            self.conf('plugins_enabled'),
            sys_plugins,
            paths=[sys_plugin_path])
        self.add_manager('plugin', plugin_manager)
        self.add_manager('collection',
                         Collection.get_instance(True))

    @staticmethod
    def get_instance(params=None):
        """ Returns the collector instance"""
        if Collector._instance is None:
            Collector._instance = Collector(params)
        return Collector._instance

    @classmethod
    def shutdown(cls):
        Collector._instance = None
        # TODO delegate shutdown

    def conf(self, key):
        """Returns the setting value for the requested key, this is a proxy
        method to the manager Config"""
        return self.managers['config'].conf(key)

    def add_manager(self, key, manager):
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
        """Adds a new file with fields *data* to the collection with id
         *collection_id* and uses the selected mapping"""
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
        return collection.save(data)

    def complete(self, collection, id_, data, force=False):
        """Completes empty fields with the non empty keys from the new data.
        If the requested file doesn't exists raises a ValueError Exception.
        If force is set to True, overrides all the keys and not only the
        empties."""
        collection = self.managers['collection'].get_collection(collection)
        fil = collection.get(id_)
        if fil is None:
            raise ValueError("File identifier not valid")
        # TODO references value
        for key, item in collection.schema.file.items():
            if item.is_multivalue():
                # TODO multivalue keys loop
                # it new data has the current field
                if key in data:
                    # the current file couldn't have the field
                    if not key in fil:
                        # if the field doesn't exists -> complete
                        complete = True
                    values = data[key]
                    if not isinstance(values, list):
                        # TODO
                        continue
                    else:
                        for i in values:
                            if not i in fil[key]:
                                if item.class_ == 'ref':
                                    # TODO reference values
                                    continue
                                else:
                                    fil[key].append(i)
                                #fil[key].append(i)
                continue
            # Check if some field exists or is empty
            complete = False
            if key in data:
                if not key in fil:
                    complete = True
                else:
                    item.set_value(fil[key])
                    complete = item.empty() or force
            if complete:
                # TODO transform value int -> str
                # str -> int or ...
                fil[key] = data[key]
        return collection.save(fil)

    def filter(self, collection, filter_):
        """Returns the collection files after apply a filter"""
        collection = self.managers['collection'].get_collection(collection)
        return collection.filter(filter_)

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
        exists = collection.filter([{'equals': [key, value]}])
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


def get_manager(name):
    """Returns a collector manager"""
    return Collector.get_instance().get_manager(name)


if __name__ == '__main__':
    Collector()
