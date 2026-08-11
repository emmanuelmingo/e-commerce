from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name="signup"),
    path('verify-email/<str:token>', views.verify_emial, name="Verify-Email")
]
