import urllib.parse

from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.reverse import reverse
from rest_framework.response import Response

from api.models import Generation


class RequestModelCreation(APIView):
    def post(self, request):
        model = request.data['model']
        fields = request.data['fields']
        requester = request.data['requester']
        staff_emails = get_user_model().staff_emails()

        # field names and values to be inserted into the url and later will be
        # inserted into the form on the admin page
        autocomplete_data = '?' + urllib.parse.urlencode(fields)

        if 'generation' in fields:
            # show gen name instead of id in email to admins
            fields['generation'] = Generation.objects.get(pk=fields['generation']).name
        # url to create new object on the admin page
        url = request.build_absolute_uri(reverse(f'admin:api_{model.lower()}_add')) + autocomplete_data
        msg = render_to_string('request_creation.html', {'first_name': requester['first_name'],
                                                         'last_name': requester['last_name'],
                                                         'username': requester['username'],
                                                         'email': requester['email'],
                                                         'model': model.lower(),
                                                         'fields': fields,
                                                         'add_model_object_url': url})
        subject = f'[REPORTER] New {model.lower()} creation request'

        # None in the from field means take sender from DEFAULT_FROM_EMAIL setting
        msg = EmailMessage(subject, msg, None, staff_emails, cc=[requester['email']])
        msg.content_subtype = 'html'
        try:
            msg.send()
            return Response()
        except Exception:
            return Response(data='Failed to send email', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

