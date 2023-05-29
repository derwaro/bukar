from django.contrib import admin
from .models import ClientSetting


# Register your models here.


class ClientSettingAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(ClientSettingAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user
        obj.save()


admin.site.register(ClientSetting, ClientSettingAdmin)
