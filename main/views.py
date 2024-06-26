from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

from main.utils import get_sarkor_datas


class SarkorScrapingAPIView(APIView):

    def get(self, request, *args, **kwargs):
        data = get_sarkor_datas()
        return Response({'status': 200, 'ctx': data})
