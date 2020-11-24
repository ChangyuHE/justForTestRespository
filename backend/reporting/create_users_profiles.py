import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reporting.settings')
django.setup()

from api.models import Profile
from django.contrib.auth import get_user_model

for user in get_user_model().objects.all():
    profiles = user.profiles.all()
    if not profiles.count():
        Profile.objects.create(name='default', user=user, active=True)
    else:
        print(list(profiles))
