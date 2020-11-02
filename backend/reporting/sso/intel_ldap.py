# -*- coding: utf-8 -*-
import ldap
import ldap.sasl


class IntelLDAP(object):
    settings = {
        'CONNECTION_OPTIONS': {
            ldap.OPT_REFERRALS: 0
        },
        'SERVER_URI': 'ldap://corpad.intel.com:3268',
        'USER_FLAGS_BY_GROUP': {},
        'USER_GROUPS_BY_GROUP': {},
        'USER_ATTR_MAP': {
            "first_name": "givenName",
            "last_name": "sn",
            "email": "mail"
        },
        'TRACE_LEVEL': 0,
        'SASL_MECH': 'DIGEST-MD5',
        'SEARCH_DN': "dc=corp,DC=intel,dc=com",
        'SEARCH_FILTER': "(SAMAccountName=%(user)s)",
    }

    def __init__(self, ldap_username, ldap_password, settings=None):
        self.ldap_username = ldap_username
        self.ldap_password = ldap_password
        if settings is not None:
            self.settings = settings

    def get_user_info(self, username):
        user_info = {}

        ldap_connection = \
            self.ldap_open_connection(self.settings['SERVER_URI'],
                                      self.ldap_username,
                                      self.ldap_password)

        ldap_user_info = self.ldap_search_user(ldap_connection, username)

        for key, value in self.settings['USER_ATTR_MAP'].items():
            if value in ldap_user_info:
                user_info[key] = ldap_user_info[value][0]

        return user_info

    def ldap_open_connection(self, ldap_url, username, password):
        ldap_session = ldap.initialize(ldap_url)

        cb_value = {
            ldap.sasl.CB_AUTHNAME: username,
            ldap.sasl.CB_PASS: password,
        }

        sasl_auth = ldap.sasl.sasl(cb_value, self.settings['SASL_MECH'])

        ldap_session.sasl_interactive_bind_s("", sasl_auth)

        for key, value in self.settings['CONNECTION_OPTIONS'].items():
            ldap_session.set_option(key, value)

        return ldap_session

    def ldap_search_user(self, connection, username):
        ldap_result_id = \
            connection.search(
                self.settings['SEARCH_DN'], ldap.SCOPE_SUBTREE,
                self.settings['SEARCH_FILTER'] % {"user": username})
        result_all_type, result_all_data = connection.result(ldap_result_id, 1)
        result_entries = []
        for result_type, result_data in result_all_data:
            if result_type is not None:
                result_entries.append(result_data)

        if len(result_entries) == 0:
            raise Exception("No entries found!")

        if len(result_entries) != 1:
            raise Exception("More than one found!")

        return result_entries[0]

