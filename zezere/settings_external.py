from configparser import ConfigParser
import os

zezere_class_path = os.path.dirname(os.path.abspath(__file__))

paths = ["%s/default.conf" % zezere_class_path, "/etc/zezere.conf", "./zezere.conf"]

parser = ConfigParser()
parser.read(paths)


def get(section, key, envvar=None):
    if envvar:
        varval = os.environ.get(envvar, None)
        if varval is not None:
            return varval

    return parser.get(section, key, fallback=None)


def getboolean(section, key, envvar=None):
    if envvar:
        varval = os.environ.get(envvar, None)
        if varval is not None:  # pragma: no cover
            return varval.lower() == "yes"

    return parser.getboolean(section, key)
