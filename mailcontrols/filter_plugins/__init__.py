from imp import load_source, load_compiled
import os
from os.path import exists, expanduser

from pkg_resources import resource_exists
from importlib import import_module


def load_filter(filter_name):
    for directory in [
        "~/.mailcontrols/filters/",
        "/var/lib/mailcontrols/filters/",
        "/etc/mailcontrols/filters/",
        "~\\AppData\\Roaming\\mailcontrols\\filters\\",
        "C:\\mailcontrols\\filters\\",
        os.path.dirname(__file__) + '/'
    ]:

        filename = expanduser("%s%s" % (directory, filter_name))
        if exists(filename + ".py"):
            return load_source(filter_name, filename + ".py")

        if exists(filename + ".pyc"):
            return load_compiled(filter_name, filename + ".pyc")

    if resource_exists(__name__, filter_name + ".pyc") or resource_exists(__name__, filter_name + ".py"):
        return import_module("mailcontrols.filter_plugins." + filter_name)

    return None
