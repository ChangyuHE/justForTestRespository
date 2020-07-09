from django import forms


class FeatureMappingFileForm(forms.Form):
    """ For debug needs only """
    file = forms.FileField(label='Select file to import')
    name = forms.CharField(required=True)
    platform = forms.IntegerField(label='Platform id', required=False)  # not required: to check empty values validation
    os = forms.IntegerField(label='Os id', required=True)
    component = forms.IntegerField(label='Component id', required=True)
    owner = forms.IntegerField(label='Owner id', required=True)
