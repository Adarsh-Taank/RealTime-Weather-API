from django.contrib import admin

# Register your models here.
from .models import city, current_weather



admin.site.register(city)

admin.site.register(current_weather)