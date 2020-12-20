"""whereithurts URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from whereithurtsapi.views import login_user, register_user, PatientViewSet, TreatmentViewSet, HurtViewSet, HealingViewSet, TreatmentTypeViewSet, BodypartViewSet, UpdateViewSet
from django.contrib import admin
from django.conf.urls import include
from django.urls import path
from rest_framework import routers

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'healings', HealingViewSet, 'healing')
router.register(r'patients', PatientViewSet, 'patient')
router.register(r'treatments', TreatmentViewSet, 'treatment')
router.register(r'hurts', HurtViewSet, 'hurt')
router.register(r'treatmenttypes', TreatmentTypeViewSet, 'treatmenttype')
router.register(r'bodyparts', BodypartViewSet, 'bodypart')
router.register(r'updates', UpdateViewSet, 'update')

urlpatterns = [
    path('', include(router.urls)),
    path('login', login_user),
    path('register', register_user),
    path('admin/', admin.site.urls),
]
