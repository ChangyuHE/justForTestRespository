import logging

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import reverse

from .forms import SelectFileForm
from .services import import_results


log = logging.getLogger(__name__)

def index(request):
    if request.method != 'POST':
        form = SelectFileForm()
    else:
        form = SelectFileForm(request.POST, request.FILES)
        if form.is_valid():
            request.session['file'] = request.FILES.get('file', None)
            request.session['validation_id'] = request.POST.get('validation_id', 0)
            return HttpResponseRedirect(reverse('collate:verify'))

    return render(request, 'collate/index.html', {'form':form})

def verify(request):
    log.debug('Begin verify.')

    file = request.session.get('file', None)
    log.debug('Retrieved file from session.')
    validation_id = int(request.session.get('validation_id', 0))

    if file is None:
        return HttpResponseRedirect(reverse('collate:index'))

    result = import_results(file, validation_id)
    if result.get('is_valid', False):
        request.session['file'] = None

    log.debug('Rendering verify.')
    return render(request, 'collate/verify.html', dict(file=file, result=result, validation_id=validation_id))
