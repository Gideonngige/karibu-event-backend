from django.contrib import admin
from .models import User, Event, Booking, Payment, Notification

# Register your models here.
admin.site.register(User)
admin.site.register(Event)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(Notification)
