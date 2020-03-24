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


class ValidationsView(APIView):
    def get(self, request, *args, **kwargs):
        ICONS = [
            'i-gen',
            'i-platform',
            (('windows',  'i-windows'), ('linux', 'i-linux')),
            (('windows', 'i-windows'), ('linux', 'i-linux')),
            'i-simulation',
            'i-validation'
        ]

        tree = Node('')

        validations_qs = Validation.objects.all().select_related('os__group', 'platform__generation', 'env')
        for validation in validations_qs.order_by('platform__generation__weight', 'platform__weight', 'os__group__name',
                                                  'os__name', 'env__name', 'name'):
            platform = validation.platform
            os = validation.os

            parent = tree
            branch = (
                {'obj': platform.generation, 'name': platform.generation.name},
                {'obj': platform, 'name': platform.short_name},
                {'obj': os.group, 'name': os.group.name},
                {'obj': os.group, 'name': os.name},
                {'obj': validation.env, 'name': validation.env.name},
                {'obj': validation, 'name': validation.name}
            )
            for v, icon_map in zip(branch, ICONS):
                icon = ''
                if isinstance(icon_map, tuple) and isinstance(v['obj'], Os):
                    for alias in icon_map:
                        if v['obj'].name.lower() == alias[0]:
                            icon = alias[1]
                else:
                    icon = icon_map
                name = v['name']

                node = find_by_attr(parent, name='text', value=name)
                if not node:
                    node = AnyNode(parent=parent, icon=icon, text=name, opened=True, selected=False)
                parent = node

        #print(RenderTree(tree))
        exporter = JsonExporter()
        d = exporter.export(tree)
        d = json.loads(d)['children']

        return Response(d)
