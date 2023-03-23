from django import forms
from .models import Treatment
from django.forms import formset_factory


class ChooseTreatmentsForm(forms.Form):
    name = forms.ModelChoiceField(queryset=Treatment.objects.filter(active=True).all())


ChooseTreatmentsFormSet = formset_factory(ChooseTreatmentsForm)
