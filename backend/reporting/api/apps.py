from django.apps import AppConfig
from django.contrib.auth import get_user_model


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        def staff_emails(cls):
            return cls.objects \
                .filter(is_staff=True) \
                .exclude(email__isnull=True) \
                .exclude(email__exact='') \
                .values_list('email', flat=True)

        UserModel = get_user_model()
        UserModel.add_to_class('staff_emails', classmethod(staff_emails))