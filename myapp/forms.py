from django import forms

class DocumentForm(forms.Form):

    docfile = forms.FileField(
        label='파일을 입력하세요.'
    )
    docfile.widget.attrs.update({'class' : 'btn btn-secondary'})