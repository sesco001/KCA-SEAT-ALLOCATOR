# --- 1. IMPORTS (Standard Library & Third Party) ---
import io
import base64
import qrcode
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Exam, SeatAssignment

# --- 2. SECURITY HELPER ---
def is_staff(user):
    """Checks if the user is an Admin or Staff member."""
    return user.is_staff

# --- 3. PUBLIC VIEWS (Accessible by Students) ---

def check_seat(request):
    """
    The homepage where students search for their seat.
    No login required.
    """
    query = request.GET.get('reg_number') # Get the number from the search box
    assignment = None
    error = None

    if query:
        try:
            # Search for the seat assignment by Student Registration Number
            assignment = SeatAssignment.objects.get(student__registration_number=query)
        except SeatAssignment.DoesNotExist:
            error = "No seat found. Check your registration number or contact admin."

    return render(request, 'check_seat.html', {'assignment': assignment, 'error': error})


def student_exam_slip(request, registration_number):
    """
    Generates the QR Code Exam Pass for the student.
    No login required (so students can print it).
    """
    # 1. Find the student's seat
    assignment = get_object_or_404(SeatAssignment, student__registration_number=registration_number)
    
    # 2. Generate the QR Code Data
    qr_data = f"Ref: {assignment.id} | Student: {assignment.student.registration_number} | Seat: {assignment.seat_number} | Room: {assignment.room.name}"
    
    # 3. Draw the image in Python memory
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    
    # 4. Convert image to a string so HTML can read it
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'exam_slip.html', {'assignment': assignment, 'qr_code': qr_image_base64})


# --- 4. RESTRICTED VIEWS (Admins & Invigilators Only) ---

@login_required
@user_passes_test(is_staff)
def exam_attendance_sheet(request, exam_id):
    """
    Generates the signing sheet for invigilators.
    PROTECTED: Requires Staff Login.
    """
    exam = get_object_or_404(Exam, id=exam_id)
    # Get all assignments for this exam, ordered by Room then Seat Number
    assignments = SeatAssignment.objects.filter(exam=exam).order_by('room__name', 'seat_number')
    
    context = {
        'exam': exam,
        'assignments': assignments,
    }
    return render(request, 'attendance_sheet.html', context)


@login_required
@user_passes_test(is_staff)
def room_door_lists(request, exam_id):
    """
    Generates the big lists to tape on doors.
    PROTECTED: Requires Staff Login.
    """
    exam = get_object_or_404(Exam, id=exam_id)
    # We fetch assignments and ORDER BY room name so Django can group them later
    assignments = SeatAssignment.objects.filter(exam=exam).order_by('room__name', 'seat_number')
    
    return render(request, 'door_lists.html', {'exam': exam, 'assignments': assignments})