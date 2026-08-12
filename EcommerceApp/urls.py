from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name="signup"),
    path('verify-email/<str:token>/', views.verify_email, name="Verify-Email"),
    path('login/', views.login, name="login")
]
