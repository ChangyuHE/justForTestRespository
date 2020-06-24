# -*- coding: utf-8 -*-
import logging

from django.contrib.auth.backends import \
    RemoteUserBackend as BaseRemoteUserBackend
from django.conf import settings
from .intel_ldap import IntelLDAP

logger = logging.getLogger()


class RemoteUserBackend(BaseRemoteUserBackend):
    def configure_user(self, user):
        intel_ldap = IntelLDAP(settings.INTEL_LDAP_USERNAME,
                               settings.INTEL_LDAP_PASSWORD)
        try:
            user_info = intel_ldap.get_user_info(user.username)
        except Exception as e:
            logger.warning("Failed to get user info: %s" % e)
        else:
            for k, v in user_info.items():
                setattr(user, k, str(v, 'utf-8'))
            user.save()

        return user

