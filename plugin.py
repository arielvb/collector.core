# -*- coding: utf-8 -*-
"""The plugin system of Collector"""

from abc import ABCMeta, abstractproperty, abstractmethod
from provider import UrlProvider
import glob
import os
import sys
import logging
from config import Config


class Plugin(object):
    """Base class for all the plugins."""
    __metaclass__ = ABCMeta

    @abstractproperty
    def get_name(self):
        """Returns the name of the plugin."""

    @abstractproperty
    def get_author(self):
        """Returns the name of the author."""

    def get_id(self):
        """Returns the identifier of the plugin."""
        return self.__class__.__name__

    @abstractproperty
    def icon(self):
        """Returns the plugin icon"""


class PluginRunnable(Plugin):
    """A plug-in that is runnable, that means that the method *run* will be
     executed when it is called or loaded if *autorun* is enabled."""

    # This is only to avoid the pylint warning:
    #  PluginRunnable.autorun: Method could be a function
    ___autorun_default = False

    @abstractmethod
    def run(self):
        """The code to run when the plugin is executed."""

    def autorun(self):
        """By default autorun is disabled."""
        return self.___autorun_default


class PluginCollector(Plugin):
    """This plugin allows recover information from websites or HTML for fill
     or discover new entries for your collections"""

    def search(self, query, provider=None):
        """Searches results that match the requested query"""
        if provider is None:
            provider = UrlProvider(self.search_uri())
        html = provider.get(query)
        return self.search_filter(html)

    def get(self, uri, provider=None):
        """Returns the collection file of the requested URI"""
        if provider is None:
            provider = UrlProvider(uri)
        html = provider.get('')
        return self.file_filter(html)

    @abstractproperty
    def search_uri(self):
        """"Returns the URI for search"""

    @abstractmethod
    def search_filter(self, html):
        """Looks for entries in the HTML code"""

    @abstractmethod
    def file_filter(self, html):
        """Looks for fields in the HTML code"""


class PluginImporter(PluginRunnable):
    """Marker for importer plugins"""


class PluginExporter(PluginRunnable):
    """Marker for exporter plugins"""


class PluginManager(object):
    """Manager for the plugin system"""

    _instance = None

    def __init__(self, enabled=None, plugins=None, paths=None):
        """PluginManager manages the avaible, enable/disable and discover
         plugins.
        Don't call directly the constructor use:
          PluginManager.get_instance()
        The arguments optional arguments of the constructor are:
         *enabled* a list of all the enabled plugins by default
         *plugins* a dictionary of plugins {id: Plugin} that are preloaded
         *paths* a list of paths to look for plugins"""
        if PluginManager._instance is not None:
            raise Exception("Called more that once")
        PluginManager._instance = self
        # else
        if plugins is None:
            plugins = {}
        if enabled is None:
            enabled = []
        self.enabled = enabled
        if paths is None:
            paths = []

        self.paths = []
        self.plugins = plugins
        self.look_for_plugins(paths)

    @staticmethod
    def get_instance(enabled=None, plugins=None, paths=None):
        """Returns the instance of the plugin manager, it will create one if it
         doesn't exits"""
        if PluginManager._instance is None:
            PluginManager._instance = PluginManager(enabled, plugins, paths)
        return PluginManager._instance

    def look_for_plugins(self, paths):
        """Discovers all the plug-ins that exists in all the paths received
         as argument"""
        # Append existing non existing paths to self.paths
        self.paths.extend([path for path in paths if path not in self.paths])
        # Look for new plug-ins
        for path in paths:
            f_path = os.path.abspath(path)
            pyfiles = glob.glob(os.path.join(f_path, '*.py'))
            # register pyfile in sys.path
            if len(pyfiles) > 0 and not f_path in sys.path:
                sys.path.append(f_path)
            # import the plugin
            for i in pyfiles:
                try:
                    module = os.path.basename(i)[:-3]
                    classname = 'Plugin' + module.capitalize()
                    temp = __import__(module,
                                      globals(), locals(),
                                      fromlist=[classname])
                    class_definition = getattr(temp, classname)
                    if issubclass(class_definition, Plugin):
                        logging.info("PluginManager: discovered plug-in %s",
                                     module)
                        plugin = class_definition()
                        self.register_plugin(plugin)
                        # Auto-execute plug-ins
                        if (issubclass(class_definition, PluginRunnable) and
                                plugin.get_id() in self.enabled and
                                plugin.autorun()):
                            plugin.run()
                except Exception as e:
                    logging.exception(e)

    def is_enabled(self, _id):
        """Checks if the plugin *_id* is enabled and if it was returns True"""
        return _id in self.enabled

    def get(self, _id):
        """Returns the plugin with identifier _id"""
        return self.plugins[_id]

    def filter(self, subclass):
        """Returns all the plugins that implements the subclass"""
        return [i for i in self.enabled
                if isinstance(self.plugins[i], subclass)]

    def get_enabled(self):
        """Returns a list of all the enabled plug-ins"""
        return self.enabled

    def get_disabled(self):
        """Returns a list with all the disabled plug-ins"""
        return [plugin for plugin in self.plugins
                if plugin not in self.enabled]

    def enable(self, pluginlist):
        """Turns on all the plug-ins of *pluginlist*, *pluginlist* must be a
         *list* of identifiers."""
        if not isinstance(pluginlist, list):
            raise TypeError()
        logging.info("Enabling plug-ins %s", pluginlist)
        for i in pluginlist:
            # Check if plug-in exists and is not yet enabled
            if i in self.plugins and i not in self.enabled:
                self.enabled.append(i)

    def disable(self, pluginlist):
        """Disables all the plug-ins which identifier is in *pluginlist*"""
        if not isinstance(pluginlist, list):
            raise TypeError()
        for i in pluginlist:
            if i in self.plugins and i in self.enabled:
                self.enabled.remove(i)

    def register_plugin(self, plugin):
        """Add to the available plug-ins the plug-in received as argument"""
        self.plugins[plugin.get_id()] = plugin

    def save(self):
        """Save the enabled plugins using config"""
        config = Config.get_instance()
        config.set('plugins_enabled', self.get_enabled())
        config.save()
