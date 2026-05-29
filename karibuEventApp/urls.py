from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('refresh_token/', views.refresh_token, name='refresh_token'),
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('verify_email/', views.verify_email, name='verify_email'),
    path('delete_account/', views.delete_account, name='delete_account'),
    path('request_reset/', views.request_reset, name='request_reset'),
    path('reset_password/', views.reset_password, name='reset_password'),
    path('send_test_email/', views.send_test_email, name='send_test_email'),
    path('auth_check/', views.auth_check, name='auth_check'),
    path('create_event/', views.create_event, name='create_event'),
    path('get_all_events/', views.get_all_events, name='get_all_events'),
    path('get_organizer_events/', views.get_organizer_events, name='get_organizer_events'),

    path("api/admin/stats/", views.admin_stats, name="admin_stats"),

    path("api/admin/events/", views.admin_events, name="admin_events"),
    path("api/admin/events/<int:id>/", views.delete_event, name="delete_event"),

    path("api/admin/users/", views.admin_users, name="admin_users"),
    path("api/admin/users/<int:id>/suspend/", views.suspend_user, name="suspend_user"),

    path("api/admin/payouts/", views.admin_payouts, name="admin_payouts"),
    path("api/admin/payouts/<int:id>/pay/", views.mark_payout_paid, name="mark_payout_paid"),

    path("api/events/<int:id>", views.get_single_event, name="get_single_event"),
    path("api/events/book", views.book_event, name="book_event"),

    path("api/events/organizer/",views.organizer_event_bookings, name="organizer_event_bookings"),
    path("api/events/verify/",views.verify_ticket,name="verify_ticket"),
]