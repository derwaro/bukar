from django.contrib import admin

from .models import Treatment
from django.contrib.auth.models import Group, User


class TreatmentAdmin(admin.ModelAdmin):
    exclude = ("user",)

    def get_queryset(self, request):
        # limit visible Treatment objects to those create by currently logged in user
        # if current user is in group "client"
        client_group = Group.objects.get(name="client")
        if "client" in list(request.user.groups.values_list("name", flat=True)):
            qs = super(TreatmentAdmin, self).get_queryset(request)
            return qs.filter(user=request.user)
        # if current user is in group superuser, return all objects
        elif request.user.username in list(
            User.objects.filter(is_superuser=True).values_list("username", flat=True)
        ):
            qs = super(TreatmentAdmin, self).get_queryset(request)
            return qs


admin.site.register(Treatment, TreatmentAdmin)
