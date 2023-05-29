from django.db import models

from django.contrib.auth.models import User

# Create your models here.


class ClientSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=150)
    address = models.CharField(max_length=250)
    servable_client = models.PositiveIntegerField()
