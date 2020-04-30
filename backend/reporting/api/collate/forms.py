from django import forms


class SelectFileForm(forms.Form):
    file = forms.FileField(label='Select file to import')
    validation_id = forms.IntegerField(label='Validation id', initial=1)
