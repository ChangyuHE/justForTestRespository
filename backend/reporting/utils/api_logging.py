from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_tracking.base_mixins import BaseLoggingMixin
from rest_framework_tracking.models import APIRequestLog

from reporting.settings import production


def get_user_object(request):
    try:
        username = request.user.username
        if not production:
            username = 'debug'
        return get_user_model().objects.get(username=username)
    except ObjectDoesNotExist:
        return request.user
    except:
        return None


class LoggingMixin(BaseLoggingMixin):
    def handle_log(self):
        self.log['username_persistent'] = get_user_object(self.request).username
        del self.log['response']
        APIRequestLog(**self.log).save()
