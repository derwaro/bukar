from django.contrib import admin

from .models import Treatment


class TreatmentAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(TreatmentAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user
        obj.save()


admin.site.register(Treatment, TreatmentAdmin)
