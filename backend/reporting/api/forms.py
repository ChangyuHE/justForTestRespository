from django import forms


class FeatureMappingFileForm(forms.Form):
    """ For debug needs only """
    file = forms.FileField(label='Select file to import')
    name = forms.CharField(required=True)
    owner = forms.IntegerField(label='Owner id', required=True)

    # extra fields are not required for testing purposes only
    codec = forms.IntegerField(label='Codec Id', required=False)
    platform = forms.IntegerField(label='Platform id', required=False)
    os = forms.IntegerField(label='Os id', required=False)
    component = forms.IntegerField(label='Component id', required=False)

