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
]