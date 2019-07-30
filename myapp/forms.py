from django import forms

class DocumentForm(forms.Form):

    docfile = forms.FileField(
        label=''
    )
    docfile.widget.attrs.update({'class' : 'btn btn-secondary'})