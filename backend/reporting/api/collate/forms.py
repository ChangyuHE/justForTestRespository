from django import forms


class SelectFileForm(forms.Form):
    file = forms.FileField(label='Select file to import')
    validation_id = forms.IntegerField(label='Validation id', initial=1, required=False)
    validation_name = forms.CharField(label='Validation name', required=False)
    validation_date = forms.DateField(label='Validation date', required=False)
    notes = forms.CharField(label='Notes', widget=forms.Textarea, required=False)
    source_file = forms.CharField(label='Source file', required=False)
    force_run = forms.BooleanField(label='Reuse Run instances', required=False)
    force_item = forms.BooleanField(label='Reuse Item instances', required=False)
