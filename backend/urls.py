from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from core.views import (
    check_seat, 
    exam_attendance_sheet, 
    room_door_lists, 
    student_exam_slip, 
    student_login, 
    unit_registration
)

# --- THE LANDING PAGE VIEW ---
def landing_page(request):
    return render(request, 'landing.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- 1. THE NEW HOMEPAGE ---
    # This MUST point to 'landing_page', NOT 'check_seat'
    path('', landing_page, name='home'),  

    # --- 2. THE SEARCH PAGE ---
    # The checker moves here
    path('search/', check_seat, name='check_seat'),

    # --- 3. OTHER LINKS ---
    path('portal/login/', student_login, name='student_login'),
    path('portal/register/', unit_registration, name='unit_registration'),
    path('slip/<path:reg_number>/', student_exam_slip, name='student_exam_slip'),
    path('print/<int:exam_id>/', exam_attendance_sheet, name='print_sheet'),
    path('door-lists/<int:exam_id>/', room_door_lists, name='door_lists'),
]