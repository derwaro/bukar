from django import forms
from .models import Treatment
from django.forms import formset_factory
from phonenumber_field.formfields import PhoneNumberField


class ChooseTreatmentsForm(forms.Form):
    name = forms.ModelChoiceField(queryset=Treatment.objects.filter(active=True).all())
    client_name = forms.CharField(
        max_length=150,
    )
    client_surname = forms.CharField(
        max_length=150,
    )
    client_mail = forms.EmailField(
        required=True,
    )
    client_phone = PhoneNumberField()


ChooseTreatmentsFormSet = formset_factory(ChooseTreatmentsForm)
