# -*- coding: utf-8 -*-


class PluginMethodNotImplemented(Exception):

    def __init__(self):
        self.value = 'Plugin method not implemented'


class PluginAbstract():

    def search(self, query):
        raise PluginMethodNotImplemented()

    def get(self, uri):
        raise PluginMethodNotImplemented()


class PluginCollector(PluginAbstract):

    def __init__(self):
        pass


class PluginManager():

    def __init__(self, enalbed):
        self.receipes = {
            'bgg': PluginCollector()
        }

        self.enabled = enalbed

    def look_for_plugins(self):
        # TODO
        import glob
        print glob.glob('/Users/arkow/universidad/pfc/app/data/user_plugins/*.py')

    def get(self, name):
        return self.receipes[name]

    def getEnabled(self):
        return self.enabled

    def getDisabled(self):
        disabled = []
        # TODO compression list
        for i in self.receipes:
            if i not in self.enabled:
                disabled.append(i)
        return disabled

    def enable(self, pluginlist):
        if not isinstance(pluginlist, list):
            raise TypeError()
        for i in pluginlist:
            # Check if plugin exists and is not yet enabled
            if i in self.receipes and i not in self.enabled:
                self.enabled.append(i)

    def disable(self, pluginlist):
        if not isinstance(pluginlist, list):
            raise TypeError()
        for i in pluginlist:
            if i in self.receipes and i in self.enabled:
                self.enabled.remove(i)
