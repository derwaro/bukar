from django.contrib import admin
from .models import ClientSettings


# Register your models here.
class ClientSettingsAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(ClientSettingsAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user
        obj.save()


admin.site.register(ClientSettings, ClientSettingsAdmin)
