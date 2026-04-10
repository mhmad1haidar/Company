from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import role_required

from .forms import CarForm, FuelLogForm, MaintenanceHistoryForm
from .models import Car, FuelLog, MaintenanceHistory


def _car_expiry_flags(car: Car, today):
    return {
        "insurance_expired": bool(car.insurance_expiry and car.insurance_expiry < today),
        "inspection_expired": bool(car.inspection_expiry and car.inspection_expiry < today),
        "registration_expired": bool(car.registration_expiry and car.registration_expiry < today),
    }


@login_required
def car_list(request):
    status = request.GET.get("status") or ""
    if status:
        cars = Car.objects.filter(status=status).order_by("-year", "plate_number")
    else:
        cars = Car.objects.all().order_by("-year", "plate_number")

    today = timezone.localdate()
    expired_ids = []
    for c in cars:
        flags = _car_expiry_flags(c, today)
        if any(flags.values()):
            expired_ids.append(c.id)

    total_cars = Car.objects.count()
    cars_in_maintenance = Car.objects.filter(status="maintenance").count()
    available_cars = Car.objects.filter(status="available").count()

    return render(
        request,
        "fleet/cars.html",
        {
            "cars": cars,
            "today": today,
            "expired_ids": set(expired_ids),
            "total_cars": total_cars,
            "cars_in_maintenance": cars_in_maintenance,
            "available_cars": available_cars,
            "status_filter": status,
        },
    )


@login_required
def car_create(request):
    if request.method == "POST":
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("/fleet/")
    else:
        form = CarForm()

    return render(request, "fleet/car_create.html", {"form": form})


@login_required
def car_detail(request, pk):
    car = get_object_or_404(Car, pk=pk)
    today = timezone.localdate()
    expiry_flags = _car_expiry_flags(car, today)

    maintenance = car.maintenance_history.all()
    fuel_logs = car.fuel_logs.all()
    usage_history = car.usage_history.select_related("intervention", "employee").all()

    maintenance_form = MaintenanceHistoryForm()
    fuel_form = FuelLogForm()

    return render(
        request,
        "fleet/car_detail.html",
        {
            "car": car,
            "expiry_flags": expiry_flags,
            "maintenance": maintenance,
            "fuel_logs": fuel_logs,
            "usage_history": usage_history,
            "today": today,
            "maintenance_form": maintenance_form,
            "fuel_form": fuel_form,
        },
    )


@login_required
def car_edit(request, pk):
    car = get_object_or_404(Car, pk=pk)

    if request.method == "POST":
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            form.save()
            return redirect(f"/fleet/{pk}/")
    else:
        form = CarForm(instance=car)

    return render(request, "fleet/car_edit.html", {"form": form, "car": car})


@login_required
def maintenance_create(request, car_id):
    """
    Backwards-compatible endpoint name used by old templates.
    POST-only: adds a maintenance record and redirects back to car detail.
    """
    if request.method != "POST":
        raise PermissionDenied("Invalid request method.")

    car = get_object_or_404(Car, pk=car_id)
    form = MaintenanceHistoryForm(request.POST)
    if form.is_valid():
        record = form.save(commit=False)
        record.car = car
        record.save()

    return redirect(f"/fleet/{car_id}/")


@login_required
def fuel_add(request, pk):
    if request.method != "POST":
        raise PermissionDenied("Invalid request method.")

    car = get_object_or_404(Car, pk=pk)
    form = FuelLogForm(request.POST)
    if form.is_valid():
        record = form.save(commit=False)
        record.car = car
        record.save()
    return redirect(f"/fleet/{pk}/")
