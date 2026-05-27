from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from rest_framework.decorators import api_view, parser_classes, permission_classes
from django.views.decorators.csrf import csrf_exempt

from .models import User, Event, Booking, Payment, Notification
from rest_framework.parsers import MultiPartParser, FormParser

from django.utils import timezone
from django.db.models import Sum, Q
from decimal import Decimal
from datetime import timedelta

from django.db.models import F, Sum, Count, DecimalField, ExpressionWrapper
from django.utils.timesince import timesince

from django.db.models.functions import TruncMonth

from .utils import send_email
import requests

import base64
import datetime
import random

import cloudinary.uploader

import os, json
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings

from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

import os
import resend
import traceback

from django.utils.html import escape
import uuid

from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, BasePermission

# indec page api
def index(request):
    return HttpResponse("Welcome to Karibu Event!.")


# sample function to send test email through sendgrid
@api_view(['POST'])
def send_test_email(request):
    to_email = request.data.get("email")
    print("Sending test email to:", to_email)
    subject = "Test Email from Karibu Event"
    html = "<h1>This is a test email from Karibu Event</h1><p>If you received this, email sending works!</p>"

    try:
        send_email(to_email, subject, html)
        return JsonResponse({"message": "Test email sent successfully"})
    except Exception as e:
        return JsonResponse({"message": "Failed to send test email", "error": str(e)}, status=500)


# email verification and password reset token generation
# signup api
@api_view(['POST'])
def signup(request):
    try:
        data = request.data

        # username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        full_name = data.get("full_name")
        phone_number = data.get("phone_number")
        role = data.get("role", "user")

        username = email

        if not all([email, password, full_name, phone_number]):
            return JsonResponse({"message": "Missing required fields"}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({"message": "Email already exists"}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"message": "Email already exists"}, status=400)

        token = str(uuid.uuid4())

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            name=full_name,
            phone_number=phone_number,
            email_verification_token=token,
            email_verified=False,
            role=role
        )

        # create welcome notification
        db_user = User.objects.get(id=user.id)
        Notification.objects.create(
            user=db_user,
            message="Welcome to Karibu Event! Your account has been created successfully.",
            is_read=False
        )

        link = f"http://192.168.100.12:8000/verify_email?token={token}"

        send_email(
            email,
            "Verify Your Karibu Event Account",
            f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; color: #333;">
        
            <h2 style="color: #2563EB;">Welcome to Karibu Event</h2>

            <p>
            Thank you for registering with Karibu Event. To complete your account setup,
            please verify your email address by clicking the button below.
            </p>

            <div style="margin: 30px 0;">
            <a href="{link}" 
               style="
                    background-color: #2563EB;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
                    display: inline-block;
               ">
                Verify Email
            </a>
            </div>

            <p>
            If the button above does not work, copy and paste the link below into your browser:
            </p>

            <p style="word-break: break-all; color: #2563EB;">
            {link}
            </p>

            <hr style="margin: 30px 0;" />

            <p style="font-size: 14px; color: #777;">
            This verification link may expire after some time for security reasons.
            </p>

            <p style="font-size: 14px; color: #777;">
            Karibu Event Team
            </p>
            </div>
            """
            )

        return JsonResponse({"message": "Account created successfully. Verify your email."}, status=201)

    except Exception as e:
        return JsonResponse({"message": "Signup failed", "error": str(e)}, status=500)

# email verification api
@api_view(['GET'])
def verify_email(request):
    token = request.GET.get("token")

    if not token:
        return render(request, "auth/email_result.html", {
            "status": "error",
            "title": "Invalid Request",
            "message": "Verification token is missing."
        })

    user = User.objects.filter(email_verification_token=token).first()

    if not user:
        return render(request, "auth/email_result.html", {
            "status": "error",
            "title": "Invalid Token",
            "message": "This verification link is invalid or has expired."
        })

    if user.email_verified:
        return render(request, "auth/email_result.html", {
            "status": "success",
            "title": "Already Verified",
            "message": "Your email is already verified."
        })

    user.email_verified = True
    user.email_verification_token = None
    user.save(update_fields=["email_verified", "email_verification_token"])

    return render(request, "auth/email_result.html", {
        "status": "success",
        "title": "Email Verified 🎉",
        "message": "Your account has been successfully verified. You can now log in."
    })


# sign in api
@api_view(['POST'])
def signin(request):
    try:
        username = request.data.get("email")
        password = request.data.get("password")

        print("Signin attempt:", {"username": username})

        if not username or not password:
            return JsonResponse({"message": "Username and password required"}, status=400)

        user = authenticate(request, username=username, password=password)

        if not user:
            return JsonResponse({"message": "Invalid credentials"}, status=401)

        if not user.email_verified:
            return JsonResponse({"message": "Verify your email first"}, status=403)

        refresh = RefreshToken.for_user(user)

        return JsonResponse({
            "message": "Login successful",
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": {
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "phone_number":user.phone_number,
                "date_joined": user.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
            }
        })

    except Exception as e:
        return JsonResponse({"message": "Login failed", "error": str(e)}, status=500)


# password reset api
@api_view(['POST'])
def request_reset(request):
    email = request.data.get("email")

    user = User.objects.filter(email=email).first()
    if not user:
        return JsonResponse({"message": "User not found"}, status=404)

    token = str(uuid.uuid4())
    user.reset_token = token
    user.save()

    link = f"http://192.168.100.12:8000/reset_password?token={token}"

    send_email(
        email,
       "Reset Your Karibu Event Password",
       f"""
       <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; color: #333;">

        <h2 style="color: #2563EB;">Password Reset Request</h2>

        <p>
            We received a request to reset your Karibu Event account password.
        </p>

        <p>
            Click the button below to create a new password:
        </p>

        <div style="margin: 30px 0;">
            <a href="{link}"
               style="
                    background-color: #DC2626;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
                    display: inline-block;
               ">
                Reset Password
            </a>
          </div>

          <p>
            If the button above does not work, copy and paste the link below into your browser:
          </p>

          <p style="word-break: break-all; color: #2563EB;">
            {link}
          </p>

          <hr style="margin: 30px 0;" />

          <p style="font-size: 14px; color: #777;">
            If you did not request a password reset, you can safely ignore this email.
          </p>

          <p style="font-size: 14px; color: #777;">
            For security reasons, this password reset link may expire after some time.
          </p>

          <p style="font-size: 14px; color: #777;">
            Karibu Event Team
          </p>

          </div>
          """
        )

    return JsonResponse({"message": "Email sent"})


# password reset api
@api_view(['GET', 'POST'])
def reset_password(request):
    token = request.GET.get("token") or request.data.get("token")

    if not token:
        return render(request, "auth/reset_result.html", {
            "status": "error",
            "message": "Missing reset token."
        })

    user = User.objects.filter(reset_token=token).first()

    if not user:
        return render(request, "auth/reset_result.html", {
            "status": "error",
            "message": "Invalid or expired reset link."
        })

    # -------------------
    # GET → show form
    # -------------------
    if request.method == "GET":
        return render(request, "auth/reset_password.html", {
            "token": token
        })

    # -------------------
    # POST → process form
    # -------------------
    password = request.data.get("password")
    confirm_password = request.data.get("confirm_password")

    if not password or not confirm_password:
        return render(request, "auth/reset_password.html", {
            "token": token,
            "error": "All fields are required"
        })

    if password != confirm_password:
        return render(request, "auth/reset_password.html", {
            "token": token,
            "error": "Passwords do not match"
        })

    user.set_password(password)
    user.reset_token = None
    user.save(update_fields=["password", "reset_token"])

    return render(request, "auth/reset_result.html", {
        "status": "success",
        "message": "Password updated successfully. You can now log in."
    })


# refresh token api
@api_view(['POST'])
def refresh_token(request):
    try:
        refresh_token = request.data.get("refresh_token")

        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)

        return JsonResponse({
            "access_token": access_token
        })

    except Exception:
        return JsonResponse({"message": "Invalid refresh token"}, status=401)

# check authentication status api
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auth_check(request):

    user = request.user

    return JsonResponse({
        "authenticated": True,
        "user": {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "phone_verified": user.phone_verified,
            "profile_image": user.profile_image,
        }
    })

# delete account api
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    try:
        user = request.user

        # Delete account
        user.delete()

        return JsonResponse({
            "message": "Account deleted successfully"
        }, status=200)

    except Exception as e:
        print("DELETE ACCOUNT ERROR:", str(e))

        return JsonResponse({
            "message": "Failed to delete account",
            "error": str(e)
        }, status=500)

# create event api
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_event(request):
    try:
        user = request.user

        # Only organizers can create events
        if user.role != "organizer":
            return JsonResponse({
                "message": "Only organizers can create events"
            }, status=403)

        data = request.data

        title = data.get("title")
        organizer_name = data.get("organizer_name")
        description = data.get("description")
        category = data.get("category")
        location = data.get("location")
        county = data.get("county")
        date = data.get("date")
        time = data.get("time")
        price = data.get("price")
        total_tickets = data.get("total_tickets")
        contact_email = data.get("contact_email")
        image = data.get("image")

        # Validation
        required_fields = [
            title,
            organizer_name,
            date,
            time,
            price,
            total_tickets,
            contact_email
        ]

        if not all(required_fields):
            return JsonResponse({
                "message": "Missing required fields"
            }, status=400)

        image_url = None
        if image:
            upload_result = cloudinary.uploader.upload(image)
            image_url = upload_result.get("secure_url")

        event = Event.objects.create(
            user=user,
            title=title,
            organizer_name=organizer_name,
            description=description,
            category=category,
            location=location,
            county=county,
            date=date,
            time=time,
            price=price,
            total_tickets=total_tickets,
            available_tickets=total_tickets,
            contact_email=contact_email,
            image=image_url
        )

        return JsonResponse({
            "message": "Event created successfully",
            "event": {
                "id": event.id,
                "title": event.title,
                "organizer_name": event.organizer_name,
                "description": event.description,
                "category": event.category,
                "location": event.location,
                "county": event.county,
                "date": str(event.date),
                "time": str(event.time),
                "price": event.price,
                "total_tickets": event.total_tickets,
                "available_tickets": event.available_tickets,
                "contact_email": event.contact_email,
                "image": event.image,
                "created_at": event.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        }, status=201)

    except Exception as e:
        return JsonResponse({
            "message": "Failed to create event",
            "error": str(e)
        }, status=500)

# get all events api
@api_view(['GET'])
def get_all_events(request):
    try:

        events = Event.objects.all().order_by('-created_at')

        # FILTERS
        search = request.GET.get("search")
        county = request.GET.get("county")
        category = request.GET.get("category")
        min_price = request.GET.get("minPrice")
        max_price = request.GET.get("maxPrice")
        date = request.GET.get("date")

        # Search by title
        if search:
            events = events.filter(title__icontains=search)

        # Filter by county
        if county:
            events = events.filter(county__icontains=county)

        # Filter by category
        if category:
            events = events.filter(category__iexact=category)

        # Filter by minimum price
        if min_price:
            events = events.filter(price__gte=min_price)

        # Filter by maximum price
        if max_price:
            events = events.filter(price__lte=max_price)

        # Filter by date
        if date:
            events = events.filter(date=date)

        event_list = []

        for event in events:

            event_list.append({
                "id": event.id,
                "title": event.title,
                "organizer_name": event.organizer_name,
                "description": event.description,
                "category": event.category,
                "location": event.location,
                "county": event.county,
                "date": str(event.date),
                "time": str(event.time),
                "price": event.price,
                "total_tickets": event.total_tickets,
                "available_tickets": event.available_tickets,
                "contact_email": event.contact_email,
                "image": event.image,
                "created_at": event.created_at.strftime("%Y-%m-%d %H:%M:%S"),

                "organizer": {
                    "id": event.user.id,
                    "name": event.user.name,
                    "email": event.user.email,
                    "phone_number": event.user.phone_number,
                }
            })

        return JsonResponse({
            "message": "Events fetched successfully",
            "count": len(event_list),
            "events": event_list
        }, status=200)

    except Exception as e:
        return JsonResponse({
            "message": "Failed to fetch events",
            "error": str(e)
        }, status=500) 


# get organizer events
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_organizer_events(request):

    try:

        user = request.user

        # Only organizers
        if user.role != "organizer":

            return JsonResponse({
                "message": "Only organizers can access this"
            }, status=403)

        events = Event.objects.filter(
            user=user
        ).order_by('-created_at')

        event_list = []

        for event in events:

            # tickets sold
            sold_tickets = (
                event.total_tickets -
                event.available_tickets
            )

            # revenue
            revenue = sold_tickets * event.price

            event_list.append({

                "id": event.id,

                "title": event.title,

                "description": event.description,

                "category": event.category,

                "county": event.county,

                "location": event.location,

                "date": str(event.date),

                "time": str(event.time),

                "price": event.price,

                "total_tickets": event.total_tickets,

                "available_tickets": event.available_tickets,

                "tickets_sold": sold_tickets,

                "revenue": revenue,

                "contact_email": event.contact_email,

                "image": event.image,

                "created_at": event.created_at.strftime("%Y-%m-%d %H:%M:%S"),

            })

        return JsonResponse({

            "message": "Organizer events fetched successfully",

            "total_events": len(event_list),

            "events": event_list

        }, status=200)

    except Exception as e:

        return JsonResponse({

            "message": "Failed to fetch organizer events",

            "error": str(e)

        }, status=500)



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, F
from .models import User, Event, Booking, Payment
import json


# =========================
# CHECK ADMIN
# =========================
def is_admin(request):
    user_id = request.headers.get("User-Id")
    print("USER ID:", user_id)

    if not user_id:
        return None

    try:
        user = User.objects.get(id=user_id)
        if user.role != "admin":
            return None
        print(f"Admin access granted for user: {user.name} (ID: {user.id})")
        return user
    except User.DoesNotExist:
        return None


# =========================
# ADMIN STATS
# GET /api/admin/stats
# =========================
@csrf_exempt
def admin_stats(request):
    if request.method != "GET":
        return JsonResponse({"message": "GET method required"}, status=405)

    admin = is_admin(request)

    if not admin:
        return JsonResponse({"message": "Unauthorized"}, status=401)

    total_users = User.objects.count()
    total_events = Event.objects.count()

    total_tickets = Booking.objects.aggregate(
        total=Sum("quantity")
    )["total"] or 0

    total_revenue = Payment.objects.filter(
        status="paid"
    ).aggregate(
        total=Sum("amount")
    )["total"] or 0

    return JsonResponse({
        "totalUsers": total_users,
        "totalEvents": total_events,
        "totalTickets": total_tickets,
        "totalRevenue": float(total_revenue),
    })


# =========================
# ADMIN EVENTS
# GET /api/admin/events
# =========================
@csrf_exempt
def admin_events(request):
    if request.method != "GET":
        return JsonResponse({"message": "GET method required"}, status=405)

    admin = is_admin(request)

    if not admin:
        return JsonResponse({"message": "Unauthorized"}, status=401)

    events = Event.objects.all().order_by("-created_at")

    events_list = []

    for event in events:
        is_past = event.date < event.created_at.date()

        status = "Active"

        if event.available_tickets <= 0:
            status = "Sold Out"
        elif is_past:
            status = "Ended"

        events_list.append({
            "id": event.id,
            "title": event.title,
            "creator": event.user.name,
            "date": event.date,
            "price": event.price,
            "status": status,
        })

    return JsonResponse({
        "events": events_list
    })


# =========================
# DELETE EVENT
# DELETE /api/admin/events/<id>
# =========================
@csrf_exempt
def delete_event(request, id):
    if request.method != "DELETE":
        return JsonResponse({"message": "DELETE method required"}, status=405)

    admin = is_admin(request)

    if not admin:
        return JsonResponse({"message": "Unauthorized"}, status=401)

    try:
        event = Event.objects.get(id=id)
        event.delete()

        return JsonResponse({
            "message": "Event deleted successfully"
        })

    except Event.DoesNotExist:
        return JsonResponse({
            "message": "Event not found"
        }, status=404)


# =========================
# ADMIN USERS
# GET /api/admin/users
# =========================
@csrf_exempt
def admin_users(request):
    if request.method != "GET":
        return JsonResponse({"message": "GET method required"}, status=405)

    admin = is_admin(request)

    if not admin:
        return JsonResponse({"message": "Unauthorized"}, status=401)

    users = User.objects.all().order_by("-date_joined")

    users_list = []

    for user in users:
        users_list.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "createdAt": user.date_joined,
            "isSuspended": not user.is_active,
        })

    return JsonResponse({
        "users": users_list
    })


# =========================
# SUSPEND USER
# PATCH /api/admin/users/<id>/suspend
# =========================
@csrf_exempt
def suspend_user(request, id):
    if request.method != "PATCH":
        return JsonResponse({"message": "PATCH method required"}, status=405)

    admin = is_admin(request)

    if not admin:
        return JsonResponse({"message": "Unauthorized"}, status=401)

    try:
        user = User.objects.get(id=id)

        if user.role == "admin":
            return JsonResponse({
                "message": "Cannot suspend admin"
            }, status=400)

        user.is_active = not user.is_active
        user.save()

        return JsonResponse({
            "message": "User updated",
            "isSuspended": not user.is_active
        })

    except User.DoesNotExist:
        return JsonResponse({
            "message": "User not found"
        }, status=404)


# =========================
# ADMIN PAYOUTS
# GET /api/admin/payouts
# =========================
@csrf_exempt
def admin_payouts(request):
    if request.method != "GET":
        return JsonResponse({"message": "GET method required"}, status=405)

    admin = is_admin(request)

    if not admin:
        return JsonResponse({"message": "Unauthorized"}, status=401)

    events = Event.objects.all()

    payouts = []

    for event in events:
        paid_amount = Payment.objects.filter(
            booking__event=event,
            status="paid"
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0

        commission = float(paid_amount) * 0.05
        payable = float(paid_amount) - commission

        payouts.append({
            "id": event.id,
            "title": event.title,
            "creator": event.user.name,
            "creatorPhone": event.user.phone_number,
            "totalRevenue": float(paid_amount),
            "commission": float(commission),
            "payable": float(payable),
            "isPaid": False,
        })

    return JsonResponse({
        "payouts": payouts
    })


# =========================
# MARK PAYOUT PAID
# PATCH /api/admin/payouts/<id>/pay
# =========================
@csrf_exempt
def mark_payout_paid(request, id):
    if request.method != "PATCH":
        return JsonResponse({"message": "PATCH method required"}, status=405)

    admin = is_admin(request)

    if not admin:
        return JsonResponse({"message": "Unauthorized"}, status=401)

    return JsonResponse({
        "message": "Payout marked as paid"
    })



from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Event, Booking, Payment, User


# ================================
# GET SINGLE EVENT
# ================================
@api_view(["GET"])
@permission_classes([AllowAny])
def get_single_event(request, id):
    try:
        event = Event.objects.get(id=id)

        data = {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "category": event.category,
            "county": event.county,
            "location": event.location,
            "date": event.date,
            "time": event.time,
            "price": event.price,
            "totalTickets": event.total_tickets,
            "availableTickets": event.available_tickets,
            "organizerName": event.organizer_name,
            "contactEmail": event.contact_email,
            "image": event.image,
            "createdAt": event.created_at,
        }

        return Response({
            "success": True,
            "event": data
        })

    except Event.DoesNotExist:
        return Response({
            "success": False,
            "message": "Event not found."
        }, status=404)


# ================================
# BOOK EVENT
# ================================
@api_view(["POST"])
@permission_classes([AllowAny])
def book_event(request):
    try:
        data = request.data

        user_id = data.get("userId")
        event_id = data.get("eventId")
        quantity = int(data.get("quantity", 1))
        phone_number = data.get("phoneNumber")

        guest_name = data.get("guestName")
        guest_email = data.get("guestEmail")

        # Validate event
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({
                "success": False,
                "message": "Event not found."
            }, status=404)

        # Validate tickets
        if event.available_tickets < quantity:
            return Response({
                "success": False,
                "message": "Not enough tickets available."
            }, status=400)

        # Logged in user
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)

                guest_name = user.name
                guest_email = user.email

            except User.DoesNotExist:
                pass

        # Guest validation
        if not guest_name:
            return Response({
                "success": False,
                "message": "Guest name is required."
            }, status=400)

        if not guest_email:
            return Response({
                "success": False,
                "message": "Guest email is required."
            }, status=400)

        total_amount = quantity * event.price

        # Create booking
        booking = Booking.objects.create(
            user=str(user.id) if user else None,
            event=event,
            guest_name=guest_name,
            guest_email=guest_email,
            quantity=quantity,
            total_amount=total_amount,
            phone_number=phone_number,
            status="confirmed"
        )

        # Reduce tickets
        event.available_tickets -= quantity
        event.save()

        booking.save()

        # Create payment record
        Payment.objects.create(
            booking=booking,
            method="M-Pesa",
            amount=total_amount,
            phone_number=phone_number,
            status="paid"
        )

        return Response({
            "success": True,
            "message": "Booking successful.",
            "booking": {
                "id": booking.id,
                "guestName": booking.guest_name,
                "guestEmail": booking.guest_email,
                "quantity": booking.quantity,
                "totalAmount": booking.total_amount,
                "phoneNumber": booking.phone_number,
                "status": booking.status,
                "createdAt": booking.created_at,
            },
            "event": {
                "id": event.id,
                "title": event.title,
                "date": event.date,
                "location": event.location,
            }
        })

    except Exception as e:
        return Response({
            "success": False,
            "message": str(e)
        }, status=500)