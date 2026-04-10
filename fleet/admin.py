from django.contrib import admin

from .models import Car, CarUsage, FuelLog, MaintenanceHistory

admin.site.register(Car)
admin.site.register(MaintenanceHistory)
admin.site.register(FuelLog)
admin.site.register(CarUsage)
