# --- 1. IMPORTS ---
import io
import base64
import qrcode
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Exam, SeatAssignment, Student, Course

# --- 2. SECURITY HELPER ---
def is_staff(user):
    return user.is_staff

# --- 3. PUBLIC VIEWS ---

def landing_page(request):
    return render(request, 'landing.html')

def check_seat(request):
    query = request.GET.get('reg_number')
    assignment = None
    error = None
    if query:
        # We just check if they exist in ANY seat to validate them
        assignment = SeatAssignment.objects.filter(student__registration_number=query).first()
        if not assignment:
            error = f"No seat found for {query}. Have you registered for units?"
    return render(request, 'check_seat.html', {'assignment': assignment, 'error': error})

# --- UPDATED: GENERATES THE MASTER DOCKET (ALL UNITS) ---
def student_exam_slip(request, reg_number):
    """Generates a Master Docket with ALL Units."""
    
    # 1. Get ALL assignments for this student (ordered by date)
    assignments = SeatAssignment.objects.filter(student__registration_number=reg_number).order_by('exam__date_time')
    
    # 2. Get the student details (Check if student exists even if no exams yet)
    student = Student.objects.filter(registration_number=reg_number).first()

    if not student:
         return render(request, 'check_seat.html', {'error': "Student not found!"})

    # 3. Generate ONE Master QR Code (Student Identity)
    qr_data = f"Student: {student.registration_number} | {student.first_name} {student.last_name}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'student_exam_slip.html', {
        'student': student,
        'assignments': assignments,  # This sends the LIST of exams to the table
        'qr_image': qr_image_base64
    })

# --- 4. STUDENT PORTAL (The Fixed Flow) ---

def student_signup(request):
    """Signup -> Auto Login -> Go to Unit Registration"""
    if request.method == 'POST':
        reg_number = request.POST.get('reg_number').strip().upper()
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        # We ignore 'course' here because the Student model doesn't store the degree name
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, 'portal/signup.html')

        if Student.objects.filter(registration_number=reg_number).exists():
            messages.error(request, "Student already exists!")
            return render(request, 'portal/signup.html')

        try:
            # 1. Create Django User (Optional, used for Admin)
            if not User.objects.filter(username=reg_number).exists():
                User.objects.create_user(
                    username=reg_number, 
                    password=password, 
                    first_name=first_name, 
                    last_name=last_name
                )

            # 2. Create Student (MATCHING YOUR MODELS.PY)
            # We generate a fake email because your model requires one.
            student_email = f"{reg_number.replace('/', '')}@student.kca.ac.ke".lower()
            
            student = Student.objects.create(
                registration_number=reg_number,
                first_name=first_name,  # Correct field
                last_name=last_name,    # Correct field
                email=student_email,    # Correct field
                password=password
            )

            # --- AUTO LOGIN HERE ---
            request.session['student_id'] = student.id
            messages.success(request, "Account created! Select your units now.")
            return redirect('unit_registration') # Go pick units

        except Exception as e:
            messages.error(request, f"Error: {e}")
            return render(request, 'portal/signup.html')

    return render(request, 'portal/signup.html')


def student_login(request):
    """Login -> Go straight to Dashboard"""
    if request.method == 'POST':
        reg_no = request.POST.get('reg_number')
        password = request.POST.get('password')
        
        try:
            student = Student.objects.get(registration_number=reg_no)
            if student.password == password:
                request.session['student_id'] = student.id
                return redirect('student_dashboard') # Go to Dashboard
            else:
                messages.error(request, "Incorrect password.")
        except Student.DoesNotExist:
            messages.error(request, "Registration number not found.")

    return render(request, 'portal/login.html')


def student_dashboard(request):
    """The Main Dashboard: Shows Enrolled Units"""
    student_id = request.session.get('student_id')
    if not student_id: return redirect('student_login')
    
    student = Student.objects.get(id=student_id)
    return render(request, 'portal/dashboard.html', {'student': student})


def unit_registration(request):
    """Select Units -> Save -> Go to Dashboard"""
    student_id = request.session.get('student_id')
    if not student_id: return redirect('student_login')
    
    student = Student.objects.get(id=student_id)
    all_courses = Course.objects.all()
    
    if request.method == 'POST':
        selected_ids = request.POST.getlist('courses')
        student.enrolled_courses.set(selected_ids)
        student.save()
        messages.success(request, "Units updated successfully!")
        return redirect('student_dashboard') # Done, go to dashboard

    return render(request, 'portal/register_units.html', {
        'student': student, 
        'all_courses': all_courses
    })

# --- 5. STAFF REPORTS ---
@login_required
@user_passes_test(is_staff)
def exam_attendance_sheet(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    assignments = SeatAssignment.objects.filter(exam=exam).order_by('room__name', 'seat_number')
    return render(request, 'attendance_sheet.html', {'exam': exam, 'assignments': assignments})

@login_required
@user_passes_test(is_staff)
def room_door_lists(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    assignments = SeatAssignment.objects.filter(exam=exam).order_by('room__name', 'seat_number')
    return render(request, 'door_lists.html', {'exam': exam, 'assignments': assignments})