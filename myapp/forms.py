from django import forms

class DocumentForm(forms.Form):

    CATEGORY_CHOICES = (
        ('', '전체'),
        ('1', '판교'),
        ('2', '백현'),
        ('3', '서현'),
        ('4', '미금'),
        ('5', '정자'),
        ('6', '서판교'),
        ('7', '수내'),
    )

    docfile = forms.FileField(
        label=''
    )
    docfile.widget.attrs.update({'class' : 'btn btn-secondary', 'onclick':'checkRegionSelected()'})

    region = forms.ChoiceField(choices = CATEGORY_CHOICES, required=True)
    region.widget.attrs.update({'class' : 'form-control', 'onchange':'retrieve()'})