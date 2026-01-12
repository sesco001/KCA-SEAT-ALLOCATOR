from django.contrib import admin
from django.urls import path
from core.views import (
    landing_page,          
    check_seat, 
    exam_attendance_sheet, 
    room_door_lists, 
    student_exam_slip, 
    student_login, 
    student_signup,        
    unit_registration,
    student_dashboard      # <--- Imported correctly
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- 1. THE NEW HOMEPAGE ---
    path('', landing_page, name='home'),  

    # --- 2. PUBLIC TOOLS ---
    path('search/', check_seat, name='check_seat'),
    path('slip/<path:reg_number>/', student_exam_slip, name='student_exam_slip'),

    # --- 3. STUDENT PORTAL ---
    path('portal/signup/', student_signup, name='student_signup'),
    path('portal/login/', student_login, name='student_login'),
    
    # --- THIS WAS MISSING ---
    path('portal/dashboard/', student_dashboard, name='student_dashboard'), 
    
    path('portal/register/', unit_registration, name='unit_registration'),

    # --- 4. STAFF REPORTS ---
    path('print/<int:exam_id>/', exam_attendance_sheet, name='print_sheet'),
    path('door-lists/<int:exam_id>/', room_door_lists, name='door_lists'),
]