import re
from typing import List, Dict, Tuple
from dataclasses import dataclass

from django.db.models import Case, When

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from api.models import Validation, Env, Os, OsGroup, Platform, Action
from utils.api_logging import LoggingMixin


__all__ = ['ReportFromSearchView']


@dataclass
class Part:
    os: str = ''
    env: str = ''
    platform: str = ''
    number: int = 2
    validation_ids: list = None


class ReportFromSearchView(LoggingMixin, APIView):
    def get(self, request, *args, **kwargs):
        # list of tuples (env_shortcut, full_env) - (sim, Simulation)
        env_names_shortnames = [(shortcut.lower(), name)
                                for shortcut, name in list(
                                    Env.objects.values_list('short_name', 'name')
                                )]
        # add list of tuples - (full_env.lower(), full_env) - (simulation, Simulation)
        envs = dict(env_names_shortnames + [
            (name.lower(), name) for _, name in env_names_shortnames
        ])

        # '19h1': 'Windows 10 19H1'
        oses = {
            shortcut: name
                for name, shortcut in Os.objects.values_list('name', 'shortcut')
            if shortcut
        }

        # {'name': 'Linux', 'aliases': 'lin,linux,ubuntu'}
        oses_groups = {alias: name
                       for name, aliases in OsGroup.objects.values_list('name', 'aliases')
                       for alias in aliases.split(',')
        }

        platforms = {}
        platform_shortnames = list(Platform.objects.values_list('short_name', flat=True))
        for i, pl in enumerate(platform_shortnames):  # create platform mapping
            name_parts = pl.split('-')  # 'tgl-lp' -> ['tgl', 'lp']
            core_platform_name = name_parts[0]
            if len(name_parts) > 1:  # if have suffix: 'lp' in 'tgl-lp' for instance
                # search for another versions of platform: 'tgl', 'tgl-lp'
                for _pl in platform_shortnames:
                    if _pl != pl and _pl.startswith(core_platform_name):
                        break  # another version is found
                else:
                    pl = core_platform_name  # no another version found
            platforms[pl.lower()] = platform_shortnames[i]  # {'ats': 'ATS', 'tgl': 'TGL-LP'}

        # to return platform in recognized query {'ATS': 'ats', 'TGL-LP': 'tgl'}
        platform_reverse_map = {val: key.upper() for key, val in platforms.items()}

        query = request.GET['query'].lower().strip()
        if not query:
            response = 'empty query'
            return Response(data=response, status=status.HTTP_400_BAD_REQUEST)

        # example: last, best, compare (reports)
        actions = list(Action.objects.values_list('name', flat=True))
        action = Action._meta.get_field('name').get_default()
        for act in actions:
            if act in query:
                action = act
                query = query.replace(action, '').strip()  # remove action from the query
        recognized_query = action

        # if have with statements -> will choose validations from different branches
        # parts of the query (branches): compare tgl lin with ats win sim
        query_parts = query.split('with')
        parts = [Part() for _ in query_parts]

        last_found_os = last_found_platform = ''
        validation_ids = []
        for query_part, part in zip(query_parts, parts):
            words = re.split(r'\s+', query_part)
            platform, found_platforms = self.extract_platform(words, platforms)
            if platform:
                last_found_platform = platform
            else:
                # in some cases we need to use platform from previous part of the query
                # example: 'compare tgl lin with win' - use tgl for both parts
                platform = last_found_platform
            env, found_envs = self.extract_env(words, envs)
            number_of_validations = 2 if len(parts) == 1 else 1
            number = self.extract_number(query_part, default_number=number_of_validations)
            os, found_oses = self.extract_os(words, env, platform, oses, oses_groups)
            if os:
                last_found_os = os

            duplicated_keywords = []
            for kw, found_values in zip(
                ['os', 'environment', 'platform'],
                [found_oses, found_envs, found_platforms]
            ):
                if len(found_values) > 1:
                    duplicated_keywords.append(f"{kw} - {', '.join(found_values)}")
            if duplicated_keywords:
                response = 'found duplicates: ' + ', '.join(duplicated_keywords)
                return Response(data=response, status=status.HTTP_400_BAD_REQUEST)
            for name, val in zip(['os', 'env', 'platform', 'number'], [os, env, platform, number]):
                setattr(part, name, val)

        # check on missing keywords
        missed = []
        if not last_found_os:
            missed.append('os')
        if not last_found_platform:
            missed.append('platform')
        if missed:
            # return hints
            hint = 'cannot find ' + ', '.join(missed)
            return Response(data=hint, status=status.HTTP_400_BAD_REQUEST)
        # recognized query for every part: '1 tgl ubuntu 18.04 silicon' for part 'tgl lin'
        recognized_parts = []
        # last os, platform are to use keywords from another parts
        # compare tgl lin with win - use tgl platform for the second part of the query
        for part in parts:
            # if os or platform is not found in this part -> use last found elements
            if part.os:
                last_found_os = part.os
            else:
                part.os = last_found_os
            if part.platform:
                last_found_platform = part.platform
            else:
                part.platform = last_found_platform
            recognized_parts.append(f' {part.number} {part.env.lower()} {part.os.lower()} '
                                    f'{platform_reverse_map[part.platform]}')
            part.validation_ids = \
                Validation.objects.filter(
                    env__name__in=[part.env],
                    platform__short_name__in=[part.platform],
                    os__name__in=[part.os]
                ).order_by('-date').values_list('id', flat=True)[:part.number]

            if not part.validation_ids:
                hint = f'no validations found for query: {part.env.lower()} ' \
                       f'{platform_reverse_map[part.platform]} {part.os.lower()}'
                return Response(data=hint, status=status.HTTP_404_NOT_FOUND)
            validation_ids += part.validation_ids
        recognized_query += ' with'.join(recognized_parts)
        if not validation_ids:
            hint = 'no validations found for query: ' + recognized_query
            return Response(data=hint, status=status.HTTP_404_NOT_FOUND)

        original_order = Case(*[When(pk=pk, then=position) for position, pk in enumerate(validation_ids)])
        validation_data = Validation.objects.filter(pk__in=validation_ids) \
            .values_list(
                'platform__generation__name', 'platform__short_name', 'os__group__name', 'os__name', 'env__name', 'name'
            ).order_by(original_order)

        return Response({
            'action': action,
            'description': recognized_query,
            'validations_data': validation_data,
            'validations_ids': validation_ids
        })

    @staticmethod
    def extract_platform(words: List[str], platforms: Dict[str, str]) -> Tuple[str, List[str]]:
        platform = ''
        found_platforms = []
        for pl in platforms:
            if pl in words:
                platform = platforms[pl]
                found_platforms.append(pl.lower())
        return platform, found_platforms

    @staticmethod
    def extract_env(words: List[str], envs: Dict[str, str]) -> Tuple[str, List[str]]:
        environment = 'Silicon'
        found_envs = []
        for env in envs:
            if env in words:
                environment = envs[env]
                found_envs.append(env)
        return environment, found_envs

    @staticmethod
    def extract_number(query: str, default_number: int) -> int:
        number = default_number
        # search for the number of validations in the beginning of the query
        found_number = re.match(r'\s*\d+', query)
        if found_number:
            number = int(found_number.group(0))
        else:
            str_numbers = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
            pattern = '|'.join(str_numbers)  # pattern - any of the numbers in list str_numbers
            found_number = re.match(pattern, query)
            if found_number:
                number = str_numbers.index(found_number.group(0)) + 1
        return number

    @staticmethod
    def extract_os(words: List[str], env: str, platform: str,
                   oses: Dict[str, str], oses_groups: Dict[str, str]) -> Tuple[str, List[str]]:
        os = ''
        found_oses = []
        # try to find specific os (search for version of os, example: 18.04 or 19h1)
        for os_ in oses:
            if os_ in words:
                os = oses[os_]
                found_oses.append(os_.lower())
        # if os isn't found -> try to find os group: win/lin/ubuntu
        if not os and platform and env:
            os_group = ''
            for os_group_ in oses_groups:
                if os_group_ in words:
                    os = oses_groups[os_group_]
                    os_group = os_group_
                    found_oses.append(os_group_.lower())
            if os:  # os group is found in query
                os_group_id = Os.objects.filter(name__in=[os]).values_list('id', flat=True)
                existed_oses = Validation.objects \
                    .filter(env__name__in=[env], platform__short_name__in=[platform]) \
                    .values_list('os', flat=True).distinct()
                os = os_group
                if existed_oses:
                    group_oses = Os.objects.filter(group__in=os_group_id, id__in=existed_oses) \
                        .order_by('-weight') \
                        .values_list('name', flat=True)
                    if group_oses:
                        os = group_oses[0]  # the latest os
        return os, found_oses
