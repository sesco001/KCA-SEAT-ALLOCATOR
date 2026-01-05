"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from core.views import check_seat, exam_attendance_sheet, room_door_lists, student_exam_slip  # <--- Import your view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', check_seat, name='check_seat'),
    path('print/<int:exam_id>/', exam_attendance_sheet, name='print_sheet'), # <--- Add this line
    path('door-lists/<int:exam_id>/', room_door_lists, name='door_lists'),
    path('slip/<str:registration_number>/', student_exam_slip, name='exam_slip'),
]
