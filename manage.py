#!/usr/bin/env python
import zezere

from sys import argv
from os import environ

if __name__ == "__main__":
    if argv[1] == "collectstatic":
        # For collectstatic, just set some auth method and key to make it not crash
        environ["AUTH_METHOD"] = "local"
        environ["SECRET_KEY"] = "collectstatic"
    zezere.run_django_management()
