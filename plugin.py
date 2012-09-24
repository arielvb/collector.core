# -*- coding: utf-8 -*-
"""The plugin system of Collector"""

from abc import ABCMeta, abstractproperty, abstractmethod
from provider import UrlProvider
import glob
import os
import sys


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


class PluginRunnable(Plugin):
    """Plugin that is runnable, that means that the method *run* will be
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
    """This plugin allows recover information from websites or html for fill
     or discover new entries for your collecions"""

    def __init__(self, provider=None):
        super(PluginCollector, self).__init__()
        if provider is None:
            provider = UrlProvider(self.search_uri())
        self.provider = provider

    def search(self, query):
        """Searchs results that match the requested query"""
        html = self.provider.get(query)
        return self.search_filter(html)

    def get(self, uri, provider=None):
        """Returns the collection file of the requestetd uri"""
        if provider is None:
            provider = UrlProvider(uri)
        html = UrlProvider()
        return self.file_filter(html)

    @abstractproperty
    def search_uri(self):
        """"Returns the uri for search"""

    @abstractmethod
    def search_filter(self, html):
        """Looks for entries in the html code"""

    @abstractmethod
    def file_filter(self, html):
        """Looks for fields in the html code"""


class PluginManager(object):
    """Manager for the plugin system"""

    def __init__(self, enabled=None, plugins=None, paths=None):
        """PluginManager manages the avaible, enable/disable and discover
         plugins.
         The arguments of the constructor, all optionals:
         *enabled* a list of all the enabled plugins by default
         *plugins* a dictionary of plugins {id: Plugin} that are preloaded
         *paths* a list of paths to look for plugins"""
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

    def look_for_plugins(self, paths):
        """Discovers all the plugins that exists in all the paths received
         as argument"""
        # TODO check for dubplicates?
        self.paths.extend(paths)
        for path in paths:
            f_path = os.path.abspath(path)
            pyfiles = glob.glob(os.path.join(f_path, '*.py'))
            # register pyfile in sys.path
            if len(pyfiles) > 0 and not f_path in sys.path:
                sys.path.append(f_path)
            # import Plugin
            for i in pyfiles:
                module = os.path.basename(i)[:-3]
                classname = 'Plugin' + module.capitalize()
                temp = __import__(module,
                                globals(), locals(),
                                  fromlist=[classname])
                class_definition = getattr(temp, classname)
                if issubclass(class_definition, Plugin):
                    # TODO log plugin loaded
                    plugin = class_definition()
                    self.register_plugin(plugin)
                    # Autoexecute plugins
                    if (issubclass(class_definition, PluginRunnable) and
                        plugin.get_id() in self.enabled and plugin.autorun()):
                        plugin.run()
        # from plugins.boardgamegeek import PluginBoardGameGeek
        #

    def get(self, _id):
        """Returns the plugin with identifier _id"""
        return self.plugins[_id]

    def is_enabled(self, _id):
        """Checks if the plugin *_id* is enalbed and if it was returns True"""
        return _id in self.enabled

    def get_enabled(self):
        """Returns a list of all the enabled plugins"""
        return self.enabled

    def get_disabled(self):
        """Returns a list with all the disabled plugins"""
        disabled = []
        # TODO compression list
        for i in self.plugins:
            if i not in self.enabled:
                disabled.append(i)
        return disabled

    def enable(self, pluginlist):
        """Turns on all the plugins of *pluginlist*, *pluginlist* must be a
         *list* of identifiers."""
        if not isinstance(pluginlist, list):
            raise TypeError()
        for i in pluginlist:
            # Check if plugin exists and is not yet enabled
            if i in self.plugins and i not in self.enabled:
                self.enabled.append(i)

    def disable(self, pluginlist):
        """Disables all the plugins which identifier is in *pluginlist*"""
        if not isinstance(pluginlist, list):
            raise TypeError()
        for i in pluginlist:
            if i in self.plugins and i in self.enabled:
                self.enabled.remove(i)

    def register_plugin(self, plugin):
        """Add to the avaible plugins the plugin received as argument"""
        self.plugins[plugin.get_id()] = plugin
