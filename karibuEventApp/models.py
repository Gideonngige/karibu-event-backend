from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, BaseUserManager

# shopkeeper model
class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(
            username=username,
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(username, email, password, **extra_fields)

# user model
class User(AbstractUser):
    ROLE_CHOICES = [
        ("user", "User"),
        ("admin", "Admin"),
        ("organizer", "Organizer"),
    ]

    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    role = models.CharField(max_length=50, default="user", choices=ROLE_CHOICES)
    username = models.CharField(max_length=150, unique=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, null=True, blank=True)
    reset_token = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'username' 
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def __str__(self):
        return f"#{self.id}  {self.name} {self.role} {self.date_joined}"


# event model
class Event(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="event")
    title = models.CharField(max_length=255)
    organizer_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    county = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField()
    time = models.TimeField()
    price = models.IntegerField()
    total_tickets = models.IntegerField()
    available_tickets = models.IntegerField()
    contact_email = models.EmailField()
    image = models.URLField(default="https://res.cloudinary.com/dc68huvjj/image/upload/v1748102584/kwwwa0avlfoeybpi3key.png")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.id} {self.title} {self.organizer_name}"


# booking model
class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("used", "Used"),
        ("cancelled", "Cancelled"),
    ]
    user = models.CharField(null=True, blank=True)
    event = models.ForeignKey("Event",on_delete=models.CASCADE,related_name="bookings")
    guest_name = models.CharField(max_length=255,null=True,blank=True)
    guest_email = models.EmailField(null=True,blank=True)
    quantity = models.IntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    qr_code = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking {self.id} {self.event.title} {self.guest_name}"


# payment model
class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]
    booking = models.ForeignKey("Booking", on_delete=models.CASCADE,related_name="payments")
    method = models.CharField(max_length=50, blank=True, null=True) 
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    phone_number = models.CharField(max_length=20)
    transaction_id = models.CharField(max_length=100, blank=True,null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")
    mpesa_receipt_number = models.CharField(max_length=100,blank=True,null=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.id} {self.amount} {self.status}"

class EventPayout(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]
    event = models.ForeignKey("Event", on_delete=models.CASCADE, related_name="payouts")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transaction_id = models.CharField(max_length=100, blank=True,null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")
    originator_conversation_id = models.CharField(max_length=100, blank=True, null=True)
    result_code = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payout #{self.id} for {self.event.title} - {self.amount} - {self.status}"

# notification model
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.name}"