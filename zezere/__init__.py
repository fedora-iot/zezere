import os
import sys


def run_django_management():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zezere.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
