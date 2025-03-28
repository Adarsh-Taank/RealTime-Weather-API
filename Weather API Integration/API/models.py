from django.db import models

# Create your models here.

class city(models.Model):
    name = models.CharField(max_length=255)
    region = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    lat = models.DecimalField(max_digits=8, decimal_places=2)
    lon = models.DecimalField(max_digits=8, decimal_places=2)
    tz_id = models.CharField(max_length=255)
    localtime_epoch = models.BigIntegerField()
    localtime = models.DateTimeField(null=True)

    def __str__(self):
        return self.name
    
class current_weather(models.Model):
    city = models.ForeignKey(city, on_delete=models.CASCADE)
    last_updated_epoch = models.BigIntegerField()
    last_updated = models.DateTimeField(null=True)
    temp_c = models.DecimalField(max_digits=5, decimal_places=2)
    temp_f = models.DecimalField(max_digits=5, decimal_places=2)
    is_day = models.SmallIntegerField()
    condition_text = models.CharField(max_length=255)
    condition_icon = models.CharField(max_length=255)
    condition_code = models.IntegerField()
    wind_mph = models.DecimalField(max_digits=5, decimal_places=2)
    wind_kph = models.DecimalField(max_digits=5, decimal_places=2)
    wind_degree = models.IntegerField()
    wind_dir = models.CharField(max_length=255)
    pressure_mb = models.DecimalField(max_digits=6, decimal_places=2)
    pressure_in = models.DecimalField(max_digits=6, decimal_places=2)
    precip_mm = models.DecimalField(max_digits=5, decimal_places=2)
    precip_in = models.DecimalField(max_digits=5, decimal_places=2)
    humidity = models.IntegerField()
    cloud = models.IntegerField()
    feelslike_c = models.DecimalField(max_digits=5, decimal_places=2)
    feelslike_f = models.DecimalField(max_digits=5, decimal_places=2)
    vis_km = models.DecimalField(max_digits=5, decimal_places=2)
    vis_miles = models.DecimalField(max_digits=5, decimal_places=2)
    uv = models.DecimalField(max_digits=5, decimal_places=2)
    gust_mph = models.DecimalField(max_digits=5, decimal_places=2)
    gust_kph = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"Weather for {self.city.name} - {self.last_updated}"
