import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reporting.settings")
django.setup()

from api.collate.issues import update_defects

if __name__ == '__main__':
    update_defects()
