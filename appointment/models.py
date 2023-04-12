from django.db import models

from django.db import models

from datetime import timedelta


# Create your models here.
class Treatment(models.Model):
    name = models.CharField(
        max_length=200, unique=True, blank=False, default="New Treatment"
    )
    price = models.IntegerField(default=0, blank=False)
    duration = models.DurationField(default="00:15:00", blank=False)
    description = models.CharField(
        max_length=500, default="This is the description of the treatment."
    )
    client_count = models.IntegerField(default=1)
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name}, {self.duration} minutes, Precio: {self.price} MXN"
