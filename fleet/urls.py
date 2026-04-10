from django.urls import path
from .views import (
    car_create,
    car_detail,
    car_edit,
    car_list,
    fuel_add,
    maintenance_create,
)

app_name = 'fleet'

urlpatterns = [
    path('', car_list, name='car_list'),
    path('create/', car_create, name='car_create'),
    path('<int:pk>/', car_detail, name='car_detail'),
    path('<int:pk>/edit/', car_edit, name='car_edit'),
    # Maintenance + fuel quick actions (from car detail page).
    path('<int:pk>/maintenance/new/', maintenance_create, name='maintenance_create'),
    path('<int:pk>/fuel/new/', fuel_add, name='fuel_add'),
]

