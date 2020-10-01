import math
import os
import typing
from datetime import datetime, timedelta
from pathlib import Path

import pytz
from django.core.exceptions import ObjectDoesNotExist
from jira import JIRA

from api.models import Issues
from reporting.settings import BASE_DIR, JIRA_SERVER, JIRA_AUTH

JIRA_CERTIFICATE = Path(BASE_DIR) / 'IntelSHA256RootCA-Base64.crt'


def get_raw_issues(query: str) -> typing.Generator:
    """Get raw data from JIRA"""
    os.environ['REQUESTS_CA_BUNDLE'] = str(JIRA_CERTIFICATE)

    jira = JIRA({'server': JIRA_SERVER, 'check_update': False, }, basic_auth=JIRA_AUTH, max_retries=2)

    # You can find custom filed id at https://jira.devtools.intel.com/rest/api/2/field
    # customfield_13801 - Closed Reason
    # customfield_13803 - Root Cause
    # customfield_19002 - Product
    # customfield_10700 - Platform/s
    # customfield_11119 - Operating System/s
    fields = "summary,description,status,priority,components,updated,customfield_19002,customfield_13801,customfield_13803,customfield_10700,customfield_11119"
    max_results = 1000
    issues = jira.search_issues(query, maxResults=max_results, fields=fields)

    for issue in issues:
        yield issue

    pending = issues.total - max_results
    if pending:
        start_at = max_results
        extra_parts = int(math.ceil(float(pending) / max_results))
        for _ in range(extra_parts):
            issues = jira.search_issues(query, maxResults=max_results, fields=fields, startAt=start_at)

            for issue in issues:
                yield issue

            start_at += max_results


class JiraDefect:
    """JIRA issue"""

    def __init__(self, raw_jira):
        self._bug = raw_jira
        self.name: str = self._bug.key

    @property
    def summary(self) -> str:
        return self._bug.fields.summary

    @property
    def status(self):
        return self._bug.fields.status.name

    @property
    def description(self):
        try:
            return self._bug.fields.description
        except AttributeError:
            return ''

    @property
    def updated(self):
        return datetime.strptime(self._bug.fields.updated, "%Y-%m-%dT%H:%M:%S.%f%z")

    @property
    def product(self):
        try:
            return self._bug.fields.customfield_19002.value
        except AttributeError:
            return []

    @property
    def closed_reason(self):
        try:
            return self._bug.fields.customfield_13801.value or ''
        except AttributeError:
            return ''

    @property
    def platforms(self):
        try:
            return [v.value for v in self._bug.fields.customfield_10700]
        except TypeError:
            return []

    @property
    def oses(self):
        try:
            return [v.value for v in self._bug.fields.customfield_11119]
        except (TypeError, AttributeError):
            return []

    @property
    def exposure(self):
        priorities = {'P1-Stopper': 4,
                      'P2-High': 3,
                      'P3-Medium': 2,
                      'P4-Low': 1,
                      'Undecided': 0}
        return priorities.get(self._bug.fields.priority.name, 0)

    @property
    def root_cause(self):
        return self._bug.fields.customfield_13803 or ''

    @property
    def components(self):
        return list({c.name for c in self._bug.fields.components})

    @property
    def self_url(self):
        return self._bug.self

    def __lt__(self, other):
        # To sort defects
        return self.name < other.name

    def to_db_record(self):
        return Issues(name=self.name,
                      self_url=self.self_url,
                      summary=self.summary,
                      description=self.description,
                      status=self.status,
                      updated=self.updated,
                      product=self.product,
                      closed_reason=self.closed_reason,
                      root_cause=self.root_cause,
                      oses=self.oses,
                      exposure=self.exposure,
                      components=self.components,
                      platforms=self.platforms)


def update_defects():
    try:
        last_updated = Issues.objects.latest('updated').updated.astimezone(pytz.timezone('Europe/Moscow'))
    except ObjectDoesNotExist:
        last_updated = datetime.now() - timedelta(days=365 * 2)

    projects = ['MDP', 'VPG SWE Media Gfx WW']
    projects = ', '.join(f'"{p}"' for p in projects)

    parts = [
        f'project in ({projects})',
        'and summary !~ "\\\\[KW\\\\]"',  # skip KlocWork
        'and type = Bug',  # we are interested only in bugs
        f'and updated >= "{last_updated.strftime("%Y-%m-%d %H:%M")}"'  # skip suites that have not been updated recently
    ]
    query = ' '.join(parts)

    updated_defects = [JiraDefect(defect).to_db_record() for defect in get_raw_issues(query)]

    fields_to_update = ['self_url', 'summary', 'description', 'status', 'updated', 'product', 'closed_reason', 'root_cause', 'oses', 'exposure', 'components', 'platforms']
    Issues.objects.bulk_update_or_create(updated_defects, fields_to_update, match_field='name')
