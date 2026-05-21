from django.contrib import admin
from .models import User, Event, Booking, Payment

# Register your models here.
admin.site.register(User)
admin.site.register(Event)
admin.site.register(Booking)
admin.site.register(Payment)
