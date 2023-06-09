#!/usr/bin/env python
import os
import sys
# from django.utils.regex_helper import _lazy_re_compile
# import django.http.request
# django.http.request.host_validation_re = _lazy_re_compile(r"[a-zA-z0-9.:]*")
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djecommerce.settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

