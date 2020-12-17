from django.shortcuts import render

from api.forms import FeatureMappingFileForm


def feature_mapping_form(request):
    form = FeatureMappingFileForm()
    return render(request, 'api/feature_mapping_import.html', {'form': form})
