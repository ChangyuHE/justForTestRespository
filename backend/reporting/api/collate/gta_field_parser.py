import abc
import asyncio
import dataclasses
import itertools
import json
import logging
import os
import re
import traceback
from dataclasses import InitVar, dataclass
from typing import Dict, Tuple

import aiohttp
import aiomisc
import requests
from aiohttp_retry import RetryClient
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage

from reporting.settings import production

log = logging.getLogger(__name__)


def custom_column(asset: str) -> Tuple[str, str]:
    return asset, f"builds[?(@.asset_key == '{asset}')]"


def custom_column_os(asset: str) -> Tuple[str, str]:
    return asset, f"execution.testRun.repro.value.tasks[?(@.name == 'setup')].items[?(@.['{asset}.asset.os_image.asset_version'])]"


CUSTOM_COLUMNS_MAPPING = dict([
    custom_column("lucas"),
    custom_column("scenario"),
    custom_column("msdk"),
    custom_column("fulsim"),
    custom_column_os("image_dut"),
    custom_column_os("simics"),
    ("driver_build_id", "build.external_id"),
    ("driver_name", "build.version"),
])


@dataclass
class Asset(abc.ABC):
    item: InitVar[Dict[str, str]]
    name: str = ''
    path: str = ''
    version: str = ''
    root: str = 'https://gfx-assets.intel.com/artifactory'

    @property
    def root_url(self) -> str:
        return self.root

    @root_url.setter
    def root_url(self, v: str) -> None:
        self.root = v[4:] if v.startswith('gta+') else v

    @property
    def is_ready(self):
        return all([self.root_url, self.path, self.name, self.version])

    def __str__(self):
        path = self.path if self.path.endswith('/') else f'{self.path}/'
        root = self.root_url if self.root_url.endswith('/') else f'{self.root_url}/'
        return f'{root}{path}{self.name}/{self.version}'

    @staticmethod
    @abc.abstractmethod
    def asset_name(self):
        pass

    def __post_init__(self, item=None):
        if item is None:
            return
        asset_jsn = item[CUSTOM_COLUMNS_MAPPING[self.asset_name()]]
        try:
            asset_jsn = json.loads(asset_jsn[0])[0]
        except IndexError:
            return
        else:
            self.root_url = asset_jsn.get('root_url', '')
            self.path = asset_jsn.get('asset_path', '')
            self.name = asset_jsn.get('asset_name', '')
            self.version = asset_jsn.get('asset_version', '')


@dataclass
class ScenarioAsset(Asset):
    def asset_name(self):
        return 'scenario'


@dataclass
class MsdkAsset(Asset):
    def asset_name(self):
        return 'msdk'


@dataclass
class OsImageAsset:
    name: str = ''
    path: str = ''
    version: str = ''
    root: str = 'https://gfx-assets.intel.com/artifactory'

    @property
    def root_url(self) -> str:
        return self.root

    @root_url.setter
    def root_url(self, v: str) -> None:
        self.root = v[4:] if v.startswith('gta+') else v

    @property
    def is_ready(self):
        return all([self.root_url, self.path, self.name, self.version])

    def __str__(self):
        path = self.path if self.path.endswith('/') else f'{self.path}/'
        root = self.root_url if self.root_url.endswith('/') else f'{self.root_url}/'
        return f'{root}{path}{self.name}/{self.version}'


@dataclass
class DutOsImageAsset(OsImageAsset):
    pass


@dataclass
class SimicsOsImageAsset(OsImageAsset):
    pass


@dataclass
class LucasAsset(Asset):
    def asset_name(self):
        return 'lucas'


@dataclass
class Driver:
    name: str = None
    build_id: str = None


@dataclass
class FulsimAsset(Asset):
    def asset_name(self):
        return 'fulsim'


@dataclass
class Simics:
    data: Dict[str, str] = dataclasses.field(default_factory=dict)


class GTAFieldParser:
    simics_re = re.compile(r'simics.asset.simics-([a-zA-Z0-9._-]*).asset_version.*', re.VERBOSE)
    lucas_version_cache = dict()
    test_run_id = None
    test_session_id = None
    mapped_component = None
    vertical = None
    platform = None
    url_list = None
    result = dict()
    auth = aiohttp.BasicAuth(settings.GTA_API_USER, settings.GTA_API_PASSWORD)

    def __init__(self, test_run_id: int, test_session_id: int,
                 mapped_component: str, vertical: str, platform: str,
                 url_list: list) -> None:
        # Do not use proxy
        os.unsetenv('HTTP_PROXY')
        os.unsetenv('HTTPS_PROXY')
        self.test_run_id = test_run_id
        self.test_session_id = test_session_id
        self.mapped_component = mapped_component
        self.vertical = vertical
        self.platform = platform
        self.url_list = url_list

    def _patch_lucas_version(self, gta_instance_url: str):
        # If Lucas version is already retrieved for currect test run ID we return cached value
        if self.test_run_id in self.lucas_version_cache.keys():
            return self.lucas_version_cache[self.test_run_id]
        s = requests.Session()
        s.auth = (settings.GTA_API_USER, settings.GTA_API_PASSWORD)
        log.debug("Started retrieving lucas version")
        # Perform requests to get LucasLog.txt
        r = s.get(f'{gta_instance_url}/api/v1/jobs/{self.test_run_id}')
        if r.status_code != 200:
            self.lucas_version_cache[self.test_run_id] = '0000'
            log.warning("Lucas version is not retrieved")
            return self.lucas_version_cache[self.test_run_id]
        jsn = r.json()
        artifacts_path = jsn['artifacts_path']
        # Parse LucasLog
        r = s.get(f'{gta_instance_url}/logs/strage/{artifacts_path}/logs/tests/0/LucasLog.txt')
        if r.status_code != 200:
            self.lucas_version_cache[self.test_run_id] = '0000'
            log.warning("Lucas version is not retrieved")
            return self.lucas_version_cache[self.test_run_id]
        lucas_log = r.text
        lucas_version = '0000'
        for line in lucas_log.splitlines():
            if line.startswith(':    LUCAS Version : '):
                lucas_version = line[21:]
                break
        self.lucas_version_cache[self.test_run_id] = lucas_version
        log.debug("Finished retrieving lucas version")
        return self.lucas_version_cache[self.test_run_id]

    def _do_post_rq(self):
        # Payload specifies data we need to GET by test run ID
        payload = {
            "globalFilterId": None,
            "compareOn": [
                "compareIdentifier",
            ],
            "filterGroups": [
                {
                    "mode": "DNF",
                    "filters": [
                        {
                            "testRun": [
                                self.test_run_id,
                            ],
                            "testSession": [
                                self.test_session_id,
                            ],
                            "mappedComponent": [
                                self.mapped_component,
                            ],
                            "vertical": [
                                self.vertical,
                            ],
                            "platform": [
                                self.platform,
                            ],
                            "tagsExcept": [
                                "notAnIssue",
                                "obsoleted",
                                "iteration",
                                "isolation",
                            ]
                        }
                    ],
                    "customColumnsFilters": {}
                }
            ],
            "diffOnly": False,
            "skipMissing": False,
            "grouped": True,
            "columns": [
                "os",
                "testRunUrl",
                "tpUrl",
                "gtaxJobId",
                "buildName",
            ],
            "customColumns": [
                CUSTOM_COLUMNS_MAPPING['lucas'],
                CUSTOM_COLUMNS_MAPPING['scenario'],
                CUSTOM_COLUMNS_MAPPING['msdk'],
                CUSTOM_COLUMNS_MAPPING['fulsim'],
                CUSTOM_COLUMNS_MAPPING['image_dut'],
                CUSTOM_COLUMNS_MAPPING['simics'],
                CUSTOM_COLUMNS_MAPPING['driver_build_id'],
                CUSTOM_COLUMNS_MAPPING['driver_name'],
            ]
        }

        async def get_amount():
            async with RetryClient(auth=self.auth) as s, s.post(
                    'http://gta.intel.com/api/results/v2/results?limit=1&offset=0&sort_by=itemName&order=ASC',
                    data=json.dumps(payload), headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    retry_attempts=20, retry_start_timeout=0.1, retry_factor=1.2,
                    retry_for_statuses=[500], raise_for_status=True,
                    retry_exceptions=[aiohttp.client_exceptions.ClientPayloadError]) as r:
                jsn = await r.json()
                log.debug(f"Started retrieving {jsn['paging']['total']} items")
                return jsn['paging']['total']

        async def fetch_url(sem: asyncio.Semaphore, limit: int, offset: int):
            async with sem:
                log.debug(f'Started request with offset {offset}')
                async with RetryClient(auth=self.auth) as s, s.post(
                        f'http://gta.intel.com/api/results/v2/results?limit={limit}&offset={offset}',
                        data=json.dumps(payload), headers={
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                        },
                        retry_attempts=20, retry_start_timeout=1, retry_factor=1.5,
                        retry_for_statuses=[500], raise_for_status=True,
                        retry_exceptions=[aiohttp.client_exceptions.ClientPayloadError]) as r:
                    jsn = await r.json()
                    res = []
                    for item in jsn['items']:
                        if item['testRunUrl'][0] in self.url_list:
                            res.append(item)
                    log.debug(f'Finished request with offset {offset}')
                    return res

        async def do_queries(amount: int):
            tasks = []
            limit = 500
            offset = 0
            sem = asyncio.Semaphore(25)
            # Pagination of async requests
            while offset < amount:
                tasks.append(asyncio.ensure_future(fetch_url(sem, limit, offset)))
                offset += limit
            responses = await asyncio.gather(*tasks)
            return list(itertools.chain.from_iterable(responses))

        amount = self.loop.run_until_complete(get_amount())
        return self.loop.run_until_complete(do_queries(amount))

    def process(self):
        with aiomisc.entrypoint() as loop:
            self.loop = loop
            try:
                self._process()
            except Exception as e:
                log.error('GTAFieldParser failed')
                if production:
                    log.info('Sending e-mail to developers')
                    stacktrace = traceback.format_exc()
                    text = f'<pre>{stacktrace}</pre>'
                    staff_emails = get_user_model().objects \
                        .filter(is_staff=True) \
                        .exclude(email__isnull=True) \
                        .exclude(email='') \
                        .values_list('email', flat=True)
                    msg = EmailMessage(
                        subject='Reporter: GTAFieldParser failure',
                        body=text,
                        from_email='lab_msdk@intel.com',
                        recipient_list=staff_emails,
                        cc=['Arseniy.Obolenskiy@intel.com'],
                    )
                    msg.content_subtype = 'html'
                    msg.send()
                raise e
            finally:
                self.loop = None

    def _process(self):
        # Do POST request to retrieve test items from GTA
        test_items = self._do_post_rq()
        test_items_amount = 0
        log.debug(f"Started processing {self.test_run_id}")

        for item in test_items:
            # Get data from test item
            driver = Driver()
            driver.name = item[CUSTOM_COLUMNS_MAPPING['driver_name']][0]
            driver.build_id = item[CUSTOM_COLUMNS_MAPPING['driver_build_id']][0]
            os = item['os'][0]
            test_item_url = item['testRunUrl'][0]
            # http://gtax-gcmxd-fm.intel.com/#/jobs/32416620#task_tests_0 -> http://gtax-gcmxd-fm.intel.com
            gta_instance_url = '/'.join(test_item_url.split('/')[:3])
            lucas = LucasAsset(item)
            scenario = ScenarioAsset(item)
            msdk = MsdkAsset(item)
            fulsim = FulsimAsset(item)
            # Get information about OS image asset
            # It can start with 'image_dut' or 'simics'
            dut_os_image = DutOsImageAsset()
            image_jsn = json.loads(item[CUSTOM_COLUMNS_MAPPING['image_dut']][0])
            if image_jsn:
                image_jsn = image_jsn[0]
                dut_os_image.root_url = image_jsn['image_dut.asset.os_image.root_url']
                dut_os_image.path = image_jsn['image_dut.asset.os_image.asset_path']
                dut_os_image.name = image_jsn['image_dut.asset.os_image.asset_name']
                dut_os_image.version = image_jsn['image_dut.asset.os_image.asset_version']
            simics_os_image = SimicsOsImageAsset()
            simics = Simics()
            image_jsn = json.loads(item[CUSTOM_COLUMNS_MAPPING['simics']][0])
            if image_jsn:
                image_jsn = image_jsn[0]
                simics_os_image.root_url = image_jsn['simics.asset.os_image.root_url']
                simics_os_image.path = image_jsn['simics.asset.os_image.asset_path']
                simics_os_image.name = image_jsn['simics.asset.os_image.asset_name']
                simics_os_image.version = image_jsn['simics.asset.os_image.asset_version']
                for key, value in image_jsn.items():
                    # Example: simics.asset.simics-5.0-2075_linux64.asset_version": "81"
                    # Added: {"5.0-2075_linux64": "81"}
                    r = self.simics_re.match(key)
                    if r:
                        simics.data[r.group(1)] = value
            # If Lucas version is not present in test item config
            # perform separate request to get Lucas version from LucasLog
            if lucas.version == '0000' or lucas.version == '':
                lucas.version = self._patch_lucas_version(gta_instance_url)
                if lucas.version == '0000':
                    lucas = LucasAsset(None)
            if msdk.version == '' or msdk.version == '0000':
                msdk = MsdkAsset(None)
            os_image = dut_os_image if dut_os_image.is_ready else simics_os_image
            # Save all retrieved fields for current test item
            self.result[test_item_url] = {
                "os": os,
                "os_image": os_image,
                "driver": driver,
                "lucas": lucas,
                "scenario": scenario,
                "msdk": msdk,
                "fulsim": fulsim,
                "simics": simics,
            }
            test_items_amount += 1
        log.debug(f"Finished processing {self.test_run_id}, added {test_items_amount} keys")
