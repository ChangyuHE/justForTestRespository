from urllib.parse import urlparse, urlunparse

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ParseError

from utils.api_logging import LoggingMixin
from utils.api_helpers import CreateWOutputApiView

from api.models import ScenarioAsset, LucasAsset, MsdkAsset, FulsimAsset

# import full and short serializer separately to make
# it easier to understand
from api.serializers import ScenarioAssetSerializer, LucasAssetSerializer, \
                            MsdkAssetSerializer, FulsimAssetSerializer
from api.serializers import ScenarioAssetFullSerializer, LucasAssetFullSerializer, \
                            MsdkAssetFullSerializer, FulsimAssetFullSerializer


def asset_view(model, full_serializer, out_serializer):
    """ Returns asset view class
        get: List of asset objects (url and id fields)
        post: Create new asset, obtain url field, returns url and id fields
    """
    return type(f'{model.__name__}View', (AbstractAssetView,),
                {'queryset': model.objects.all(),
                 'serializer_class': full_serializer,
                 'serializer_output_class': out_serializer})


class AbstractAssetView(LoggingMixin, generics.ListAPIView, CreateWOutputApiView):
    serializer_output_class = None
    serializer_class = None

    def post(self, request, *args, **kwargs):
        url = request.data['url']
        url_components = url.split('/')
        if len(url_components) == 1:
            # asset name is provided
            data = data = {'root': '', 'path': '', 'name': url_components[0], 'version': ''}
        else:
            # full url is provided
            parsed_url = urlparse(url)
            path = parsed_url.path if not parsed_url.path.startswith('/') else parsed_url.path[1:]
            path_components = path.split('/')
            if not parsed_url.scheme or not parsed_url.netloc or not path_components[0]:
                raise ParseError('Cannot parse url scheme or server')
            if len(path_components) < 3:
                raise ParseError("The path should contains '/artifactory/', asset name and version")

            root = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                path_components[0],
                '',
                '',
                ''
            ))

            name, version = path_components[-2:]
            pure_path = '/'.join(path_components[1:-2])
            data = {'root': root, 'path': pure_path, 'name': name, 'version': version}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return self.serializer_output_class
        return self.serializer_class


# generate template views for Assets
# get: list of asset objects
# post: create asset object
ScenarioAssetView = asset_view(ScenarioAsset, ScenarioAssetFullSerializer, ScenarioAssetSerializer)
LucasAssetView = asset_view(LucasAsset, LucasAssetFullSerializer, LucasAssetSerializer)
MsdkAssetView = asset_view(MsdkAsset, MsdkAssetFullSerializer, MsdkAssetSerializer)
FulsimAssetView = asset_view(FulsimAsset, FulsimAssetFullSerializer, FulsimAssetSerializer)
