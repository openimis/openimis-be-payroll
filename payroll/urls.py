from django.urls import path

from .views import send_callback_to_openimis

urlpatterns = [
    path('send_callback_to_openimis/', send_callback_to_openimis),
]

