import json
from datetime import datetime, timezone

import dateutil.parser

from django.db import transaction
from django.db.models import Q

from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

import anytree.search
from anytree import Node
from anytree.exporter import JsonExporter

from api.models import Validation, Result, Run, FeatureMapping, Generation, Platform, Os
from api.serializers import ValidationSerializer, ValidationUpdateSerializer, OsSerializer, \
                            FeatureMappingSerializer, GenerationSerializer, PlatformSerializer
from utils.api_logging import get_user_object, LoggingMixin

__all__ = [
    'ValidationsView', 'ValidationsFlatView', 'ValidationsStructureView',
    'ValidationsDeleteByIdView', 'ValidationUpdateDeleteView', 'ValidationDetailsView',
    'ValidationMappings'
]

ICONS = [
    'mdi-expansion-card',                                               # gen
    'mdi-chip',                                                         # platform
    (('windows', 'mdi-microsoft-windows'), ('linux', 'mdi-linux')),     # os group
    (('windows', 'mdi-microsoft-windows'), ('linux', 'mdi-linux')),     # os
    'mdi-memory',                                                       # env
    'mdi-select-group',                                                 # validation type
    'mdi-format-list-bulleted-type'                                     # validation
]


class ValidationsView(LoggingMixin, APIView):
    def get(self, request, *args, **kwargs):
        filters_data = request.GET.get('data', {})
        if filters_data:
            filters_data = json.loads(filters_data)
            for f in filters_data:
                if all(key in f for key in ['start', 'end']):
                    f['start'] = dateutil.parser.isoparse(f['start'])
                    f['end'] = dateutil.parser.isoparse(f['end'])

        tree = Node('')

        validations_qs = Validation.objects.all() \
            .select_related('os__group', 'platform__generation', 'env', 'owner')
        for validation in validations_qs.order_by('-platform__generation__weight',
                                                  'platform__weight', 'os__group__name',
                                                  'os__name', 'env__name', 'name'):
            # shortcuts
            platform = validation.platform
            os = validation.os

            # tree branch data: gen -> platform -> os.group -> os -> env -> validation name
            branch = (
                {'obj': platform.generation, 'name': platform.generation.name, 'level': 'gen'},
                {'obj': platform, 'name': platform.short_name, 'level': 'platform'},
                {'obj': os.group, 'name': os.group.name, 'level': 'os_group'},
                {'obj': os.group, 'name': os.name, 'level': 'os'},
                {'obj': validation.env, 'name': validation.env.name, 'level': 'env'},
                {'obj': validation.type, 'name': validation.type.name, 'level': 'validation_type'},
                {'obj': validation, 'name': validation.name, 'level': 'validation'}
            )

            # filter by input data
            if filters_data:
                ok = []
                for f in filters_data:
                    # date range check
                    if all(key in f for key in ['start', 'end']):
                        ok.append(f['start'] <= validation.date <= f['end'])

                    # tree levels check
                    else:
                        for node in branch:
                            if node['level'] == f['level']:
                                # validation name pattern check
                                if f['level'] == 'validation':
                                    if f['value'].lower() in node['name'].lower():
                                        ok.append(True)
                                        break
                                else:
                                    # filter by id
                                    if node['obj'].id in f['value']:
                                        ok.append(True)
                                        break

                            # filter validation nodes by owner/component/feature
                            if node['level'] == 'validation':
                                if f['level'] == 'user' and node['obj'].owner.id in f['value']:
                                    ok.append(True)
                                    break
                                if f['level'] == 'component' and \
                                        set(node['obj'].components) & set(f['value']):
                                    ok.append(True)
                                    break
                                if f['level'] == 'feature' and \
                                        set(node['obj'].features) & set(f['value']):
                                    ok.append(True)
                                    break
                        else:
                            ok.append(False)

                if not all(ok):
                    continue

            parent = tree
            for node_data, icon_map in zip(branch, ICONS):
                # set icon according to tree level ICONS mapping
                icon, name = '', ''
                if isinstance(icon_map, tuple):
                    for alias in icon_map:
                        if node_data['obj'].name.lower() == alias[0]:
                            icon = alias[1]
                else:
                    icon = icon_map
                name = node_data['name']

                node_main_params = {
                    'parent': parent,
                    'name': name,
                    'text': name,
                    'text_flat': name,
                    'selected': False,
                    'opened': True,
                    'level': node_data['level'],
                    'id': node_data['obj'].id,
                    'klass': type(node_data['obj']).__name__,
                    'icon': f'{icon} mdi tree-icon'
                }
                node_validation_params = {
                    'passed': validation.passed,
                    'failed': validation.failed,
                    'error': validation.error,
                    'blocked': validation.blocked,
                    'skipped': validation.skipped,
                    'canceled': validation.canceled,
                    'owner': validation.owner.id,
                    'date': validation.date.strftime('%a %b %d %Y')
                }

                # find node by name and level, if not create new one
                node = anytree.search.find(parent,
                    lambda n: n.name == name and n.level == node_data['level']
                )
                if not node:
                    if node_data['level'] == 'validation':
                        node = Node(**node_main_params, **node_validation_params)
                    else:
                        node = Node(**node_main_params)
                parent = node

        exporter = JsonExporter()
        d = exporter.export(tree)

        # cut off root level to have Generation as first one on frontend
        d = json.loads(d).get('children', [])
        return Response(d)


class IsAdminOrOwner(permissions.BasePermission):
    message = 'Validation owner or admin can perform this action only'

    def has_object_permission(self, request, view, obj):
        user = get_user_object(request)

        if obj.owner == user or user.is_staff:
            return True
        return False


class ValidationDetailsView(LoggingMixin, generics.RetrieveAPIView):
    """ Retrieve validation object """

    queryset = Validation.objects.all()
    serializer_class = ValidationSerializer


class ValidationUpdateDeleteView(LoggingMixin, generics.UpdateAPIView, generics.DestroyAPIView):
    """
        patch: Update Validation object
        put: Update Validation object
        delete: Soft-delete of validation object
    """
    queryset = Validation.objects.all()
    serializer_class = ValidationUpdateSerializer
    permission_classes = [IsAdminOrOwner]

    # soft-delete
    def perform_destroy(self, instance):
        instance.deleted = datetime.now(timezone.utc)
        instance.save()


class ValidationsDeleteByIdView(LoggingMixin, generics.DestroyAPIView):
    queryset = Validation.all_objects.all()
    permission_classes = [IsAdminOrOwner]

    @transaction.atomic
    def perform_destroy(self, instance):
        # get list of runs for this validation
        run_ids = list(
            Result.objects.filter(validation=instance).values_list('run', flat=True).distinct()
        )

        # delete Validation object and linked Result objects due to cascade on_delete
        instance.delete()

        # detect unattended runs and delete them
        for run_id in run_ids:
            if Result.objects.filter(run_id=run_id).count() == 0:
                Run.objects.get(pk=run_id).delete()


class ValidationsFlatView(LoggingMixin, APIView):
    def get(self, request, *args, **kwargs):
        d = []
        ids = request.GET.get('ids', '')
        if ids:
            id_list = ids.split(',')
            validations_qs = Validation.objects.filter(id__in=id_list).order_by('-id')
        else:
            validations_qs = Validation.objects.all().order_by('-id')
        for v in validations_qs:
            d.append({
                'name': f'{v.name} ({v.platform.name}, {v.env.name}, {v.os.name})',
                'id': v.id
            })
        return Response(d)


def get_mappings_by_validations(serializer_class, validations, user):
    """ Filter mappings according to validation's platform, os and component from validation results """
    data = []
    components = Result.objects.filter(validation__in=validations) \
                       .values_list('component', flat=True).distinct()
    for validation in validations:
        mappings = FeatureMapping.objects.filter(
            Q(component__in=components, platform=validation.platform, os=validation.os.group),
            Q(public=True) | Q(owner=user)
        )
        serializer = serializer_class(data=mappings, many=True)
        serializer.is_valid()

        for serialized_data in serializer.data:
            if serialized_data not in data:
                data.append(serialized_data)
    return data


class ValidationMappings(LoggingMixin, generics.GenericAPIView):
    serializer_class = FeatureMappingSerializer

    def get_queryset(self):
        ids = self.request.query_params.get('ids', None)
        if ids is not None:
            ids = [int(x) for x in ids.split(',')]
            return Validation.objects.filter(pk__in=ids)
        else:
            return Validation.objects.all()

    def get(self, request, *args, **kwargs):
        validations = self.get_queryset()
        return Response(
            get_mappings_by_validations(self.serializer_class,
                                        validations,
                                        get_user_object(request))
        )


class ValidationsStructureView(LoggingMixin, APIView):
    def get(self, request, *args, **kwargs):
        d = [
            {'level': 'gen', 'label': 'Generation', 'items': []},
            {'level': 'platform', 'label': 'Platform', 'items': []},
            {'level': 'os_group', 'label': 'OS Family', 'items': []},
            {'level': 'os', 'label': 'OS', 'items': []}
        ]
        gens = Generation.objects.filter(
            id__in=Validation.objects.values_list('platform__generation', flat=True)
                .order_by('-platform__generation__weight').distinct())
        d[0]['items'] = GenerationSerializer(gens, many=True).data

        platforms = Platform.objects.filter(
            id__in=Validation.objects.values_list('platform', flat=True)
                .order_by('-platform__weight').distinct())
        d[1]['items'] = PlatformSerializer(platforms, many=True).data

        os_groups = Os.objects.filter(
            id__in=Validation.objects.values_list('os__group', flat=True)
                .order_by('os__group__name').distinct())
        d[2]['items'] = OsSerializer(os_groups, many=True).data

        oses = Os.objects.filter(
            id__in=Validation.objects.values_list('os', flat=True).order_by('os__name').distinct())
        d[3]['items'] = OsSerializer(oses, many=True).data

        return Response(d)
