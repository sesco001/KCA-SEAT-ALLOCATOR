# --- 1. IMPORTS ---
import io
import base64
import qrcode
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User  # <--- Added for creating users
from django.contrib import messages
from .models import Exam, SeatAssignment, Student, Course

# --- 2. SECURITY HELPER ---
def is_staff(user):
    return user.is_staff

# --- 3. PUBLIC VIEWS (Landing, Search & Tickets) ---

def landing_page(request):
    """The Main Homepage with links to Portal and Check Seat."""
    return render(request, 'landing.html')

def check_seat(request):
    """Search for seat by Reg Number."""
    query = request.GET.get('reg_number')
    assignment = None
    error = None

    if query:
        # Filter assignments by the student reg number
        # We use .first() to get the first exam found (simplistic search)
        assignment = SeatAssignment.objects.filter(student__registration_number=query).first()
        
        if not assignment:
            error = f"No seat found for {query}. Have you registered for units?"

    return render(request, 'check_seat.html', {'assignment': assignment, 'error': error})


def student_exam_slip(request, reg_number):
    """Generates the QR Code Ticket."""
    assignment = SeatAssignment.objects.filter(student__registration_number=reg_number).first()
    
    if not assignment:
        return render(request, 'check_seat.html', {'error': "No exams found for this student."})

    # Generate QR Data
    qr_data = f"ID: {assignment.student.registration_number} | Seat: {assignment.seat_number} | Room: {assignment.room.name}"
    
    # Create Image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'student_exam_slip.html', {
        'student': assignment.student,
        'assignment': assignment, 
        'qr_image': qr_image_base64
    })

# --- 4. STUDENT PORTAL (Signup, Login & Registration) ---

def student_signup(request):
    """Allows new students to register themselves."""
    if request.method == 'POST':
        reg_number = request.POST.get('reg_number').strip().upper()
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        course_name = request.POST.get('course')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # 1. Password Match Check
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, 'portal/signup.html')

        # 2. Duplicate Check
        if Student.objects.filter(registration_number=reg_number).exists():
            messages.error(request, "Student with this Reg Number already exists!")
            return render(request, 'portal/signup.html')

        try:
            # 3. Create Django User (Optional, but good for Admin integration)
            if not User.objects.filter(username=reg_number).exists():
                User.objects.create_user(username=reg_number, password=password, first_name=first_name, last_name=last_name)

            # 4. Create the Student Profile (This enables login)
            Student.objects.create(
                registration_number=reg_number,
                name=f"{first_name} {last_name}",
                course_name=course_name,
                password=password # Saving here so student_login works
            )

            messages.success(request, "Account created successfully! Please Login.")
            return redirect('student_login')

        except Exception as e:
            messages.error(request, f"Error creating account: {e}")
            return render(request, 'portal/signup.html')

    return render(request, 'portal/signup.html')


def student_login(request):
    """The Gate: Simple login for students."""
    if request.method == 'POST':
        reg_no = request.POST.get('reg_number')
        password = request.POST.get('password')
        
        try:
            student = Student.objects.get(registration_number=reg_no)
            # Verify password (matches what was saved in signup)
            if student.password == password:
                request.session['student_id'] = student.id # Save ID in session
                return redirect('unit_registration')
            else:
                messages.error(request, "Incorrect password.")
        except Student.DoesNotExist:
            messages.error(request, "Registration number not found.")

    return render(request, 'portal/login.html')


def unit_registration(request):
    """The Form: Students tick the units they are doing."""
    # 1. Protect the view (Must be logged in)
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('student_login')
    
    student = Student.objects.get(id=student_id)
    all_courses = Course.objects.all()
    
    if request.method == 'POST':
        # 2. Get checked boxes
        selected_ids = request.POST.getlist('courses')
        
        # 3. Update the ManyToMany field (The Automation!)
        student.enrolled_courses.set(selected_ids)
        student.save()
        
        return render(request, 'portal/dashboard.html', {'student': student, 'success': True})

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
