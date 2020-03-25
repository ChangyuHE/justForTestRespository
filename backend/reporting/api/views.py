import copy
import json
import time
import yaml
import django_filters.rest_framework

from collections import defaultdict

from jinja2 import Environment, PackageLoader

from django.views.generic import TemplateView
from django.shortcuts import render, get_object_or_404
from django.forms.models import model_to_dict
from django.views.decorators.cache import never_cache

from rest_framework import generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import *
from .models import Os

from reporting.settings import production

from anytree import Node, RenderTree, AnyNode
from anytree.search import find_by_attr
from anytree.exporter import JsonExporter


@never_cache
def index(request):
    return render(request, 'api/index.html', {})


# all requests that should managed by vue just pass to index
class PassToVue(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'api/index.html', {})


ICONS = [
    'i-gen',
    'i-platform',
    (('windows',  'i-windows'), ('linux', 'i-linux')),
    (('windows', 'i-windows'), ('linux', 'i-linux')),
    'i-simulation',
    'i-validation'
]


class ValidationsView(APIView):
    def get(self, request, *args, **kwargs):
        tree = Node('')

        validations_qs = Validation.objects.all().select_related('os__group', 'platform__generation', 'env')
        for validation in validations_qs.order_by('platform__generation__weight', 'platform__weight', 'os__group__name',
                                                  'os__name', 'env__name', 'name'):
            # shortcuts
            platform = validation.platform
            os = validation.os

            # tree branch data: gen -> platform -> os.group -> os -> env -> validation name
            branch = (
                {'obj': platform.generation, 'name': platform.generation.name, 'level': 0},
                {'obj': platform, 'name': platform.short_name, 'level': 1},
                {'obj': os.group, 'name': os.group.name, 'level': 2},
                {'obj': os.group, 'name': os.name, 'level': 3},
                {'obj': validation.env, 'name': validation.env.name, 'level': 4},
                {'obj': validation, 'name': validation.name, 'level': 5}
            )

            parent = tree
            for node_data, icon_map in zip(branch, ICONS):
                # according to ICONS structure detect which icon should be used for each level
                icon, name = '', ''
                if isinstance(icon_map, tuple):
                    for alias in icon_map:
                        if node_data['obj'].name.lower() == alias[0]:
                            icon = alias[1]
                else:
                    icon = icon_map
                name = node_data['name']

                # find node, if not create new one
                node = find_by_attr(parent, name='text', value=name)
                if not node:
                    node = AnyNode(
                        parent=parent, icon=icon, text=name, selected=False,
                        opened=True if node_data['level'] < 2 else False
                    )
                parent = node

        exporter = JsonExporter()
        d = exporter.export(tree)

        # cut off first level, frontend requirement
        d = json.loads(d)['children']
        return Response(d)
