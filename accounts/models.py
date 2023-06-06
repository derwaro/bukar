from django.db import models

from django.contrib.auth.models import User
from django.template.defaultfilters import slugify

# Create your models here.


class ClientSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=150, unique=True)
    company_name_slug = models.SlugField(
        max_length=150, default=slugify(company_name), editable=False, unique=True
    )
    address = models.CharField(max_length=250)
    servable_client = models.PositiveIntegerField()
    calendar_id = models.CharField(max_length=90)
    calendar_email = models.EmailField(default="email@example.com")

    def __str__(self):
        return f"{self.user} with <{self.company_name}> at <{self.company_name_slug}>"

    def save(self, *args, **kwargs):
        self.company_name_slug = slugify(self.company_name)
        self.calendar_email = self.user.email
        super(ClientSetting, self).save(*args, **kwargs)
