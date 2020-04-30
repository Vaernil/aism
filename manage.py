#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# podzielenie na dev i produkcje
# każda komenda z manage.py wymaga wiec dodania argumentu
# narazie różnią się tylko ustawieniem zmiennej DEBUG
# startuj ze skryptu ./start_dev

#  pamiętaj jednak, że bez DEBUG = True django nie ładuje plików statycznych
#  a więc cssa, jsa itd.
#  https://stackoverflow.com/questions/5836674/why-does-debug-false-setting-make-my-django-static-files-access-fail
def main():
    # jeśli ostatnim argumentem jest 'dev'
    if sys.argv[-1] == 'dev':
        print("Ładowanie ustawień 'dev'")
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aism_ag.settings_dev')
    # jesli nie ma zadnego argumentu wyrzuc error do terminala
    #  elif len(sys.argv) < 2:
    elif sys.argv[-1] == '':
        print("Musisz dodać argument")
    else:
        # napisz do konsoli
        print("")
        if sys.argv[-1] != 'prod':
            sys.argv.append('prod')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aism_ag.settings')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv[:-1])


if __name__ == '__main__':
    main()
