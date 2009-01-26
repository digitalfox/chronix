# -*- coding: utf-8 -*-
"""
Plugin management helpers

@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license:GNU GPL V3
"""

def loadPlugin(base, pluginName):
    """Load a plugin class from standard chronix plugin structure
    Ex. usage:
    queueType=loadPlugin("jobqueue", "standard.RandomJobQueue")
    queue=queueType()
    @param base: base name of plugin. Ex. "jobqueue". It is the package just in chronix/plugins directory
    @type base: str
    @param pluginName: name of plugin with the following syntax: module.class. Ex. "standard.FifoJobQueue"
    @type pluginName: str
    @return: plugin type
    @raise ChronixPluginException: """
    # Add dot if needed
    if not base[-1]==".":
        base+="."
    try:
        # Load module
        m=__import__("chronix.plugins."+base+pluginName.split(".")[0])
        # Create type
        return eval("m.plugins."+base+pluginName)
    except (AttributeError, NameError, ImportError), e:
        msg="Cannot load %s plugin named %s (%s)" % (base[0:-1], pluginName, e)
        raise ChronixPluginException(msg)

class ChronixPluginException(Exception):
    """Exception raised when a plugin cannot be correctly loaded"""
    pass