from django import forms

class DocumentForm(forms.Form):
    docfile = forms.FileField(
        label='파일을 입력하세요.',
        help_text='용량제한 42M'
    )