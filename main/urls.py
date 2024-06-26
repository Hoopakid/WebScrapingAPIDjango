from django.urls import path

from main.views import SarkorScrapingAPIView

urlpatterns = [
    path('get-sarkor-data', SarkorScrapingAPIView.as_view(), name='get-sarkor-data')
]
