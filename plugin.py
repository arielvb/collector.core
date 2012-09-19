# -*- coding: utf-8 -*-
from abc import *
from provider import UrlProvider


class Plugin(object):

    __metaclass__ = ABCMeta

    @abstractproperty
    def get_name(self):
        pass

    @abstractproperty
    def get_author(self):
        pass

    def get_id(self):
        return self.__class__.__name__


class PluginRunnable(Plugin):

    @abstractmethod
    def run():
        pass

    def autorun(self):
        return False


class PluginCollector(Plugin):

    def __init__(self, provider=None):
        super(PluginCollector, self).__init__()
        if provider is None:
            provider = UrlProvider(self.search_query)
        self.provider = provider

    def search(self, query):
        self.results = self.provider.get(query)

    def get(self, uri):
        pass

    @abstractmethod
    def search_filter(self, html):
        pass

    @abstractmethod
    def attr_filter(self, html):
        pass


import glob
import os
import sys


class PluginManager(object):

    plugins = {}
    paths = []
    enabled = []

    def __init__(self, enabled=[], plugins=None, paths=[]):
        if plugins is not None:
            self.plugins = plugins
        self.enabled = enabled
        self.look_for_plugins(paths)

    def look_for_plugins(self, paths):
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

    def get(self, name):
        return self.plugins[name]

    def isEnabled(self, name):
        return name in self.enabled

    def getEnabled(self):
        return self.enabled

    def getDisabled(self):
        disabled = []
        # TODO compression list
        for i in self.plugins:
            if i not in self.enabled:
                disabled.append(i)
        return disabled

    def enable(self, pluginlist):
        if not isinstance(pluginlist, list):
            raise TypeError()
        for i in pluginlist:
            # Check if plugin exists and is not yet enabled
            if i in self.plugins and i not in self.enabled:
                self.enabled.append(i)

    def disable(self, pluginlist):
        if not isinstance(pluginlist, list):
            raise TypeError()
        for i in pluginlist:
            if i in self.plugins and i in self.enabled:
                self.enabled.remove(i)

    def register_plugin(self, plugin):
        self.plugins[plugin.get_id()] = plugin
