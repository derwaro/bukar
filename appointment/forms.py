from django import forms
from .models import Treatment
from django.contrib.auth.models import User
from accounts.models import ClientSetting
from django.forms import formset_factory
from phonenumber_field.formfields import PhoneNumberField


class ChooseTreatmentsForm(forms.Form):
    name = forms.ModelChoiceField(queryset=Treatment.objects.none())
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

    def __init__(self, *args, **kwargs):
        company_name = kwargs.pop("company_name")
        super().__init__(*args, **kwargs)
        self.fields["name"].queryset = Treatment.objects.filter(
            user__clientsetting__company_name=company_name, active=True
        )


ChooseTreatmentsFormSet = formset_factory(ChooseTreatmentsForm)
