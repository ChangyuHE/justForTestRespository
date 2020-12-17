from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache


@never_cache
def index(request):
    return render(request, 'api/index.html', {})


@never_cache
def test(request):
    return render(request, 'api/test.html', {})


# all requests that should managed by vue just pass to index
class PassToVue(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'api/index.html', {})
