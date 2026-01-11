from django.core.management.base import BaseCommand
from core.models import Exam, Room, SeatAssignment

class Command(BaseCommand):
    help = 'Allocates seats for a specific exam with Anti-Collision Logic'

    def add_arguments(self, parser):
        parser.add_argument('exam_id', type=int, help='ID of the exam to allocate')

    def handle(self, *args, **options):
        exam_id = options['exam_id']
        
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Exam ID {exam_id} not found!'))
            return

        self.stdout.write(f"Starting allocation for: {exam}...")

        # 1. Clear old assignments for this specific exam
        SeatAssignment.objects.filter(exam=exam).delete()

        # 2. GET STUDENTS (FIXED HERE)
        # We now get students via the Course they enrolled in.
        # "exam.registered_students" is deleted, so we use "exam.course.students"
        all_students = exam.course.students.all()
        
        if not all_students.exists():
             self.stdout.write(self.style.WARNING(f"No students found! Did they register for {exam.course.name} in the portal?"))
             return

        # Separate priorities
        special_needs_students = all_students.filter(has_special_needs=True)
        regular_students = all_students.filter(has_special_needs=False)

        # 3. Get all rooms (Accessible first)
        all_rooms = Room.objects.all().order_by('-is_accessible', '-capacity') 

        # 4. The Allocation Loop
        student_queue = list(special_needs_students) + list(regular_students)
        
        rooms_iter = iter(all_rooms)
        current_room = next(rooms_iter, None)
        seats_filled_in_room = 0

        # Track success count for report
        assigned_count = 0

        for student in student_queue:
            
            # --- ANTI-CLASH CHECK ---
            # Check if student is busy at this EXACT time in another exam
            conflict = SeatAssignment.objects.filter(
                student=student,
                exam__date_time=exam.date_time
            ).exclude(exam=exam).exists()

            if conflict:
                self.stdout.write(self.style.ERROR(f"CRITICAL CONFLICT: {student} has another exam at {exam.date_time}! Skipping."))
                continue 

            # Room Availability Check
            if not current_room:
                self.stdout.write(self.style.ERROR('CRITICAL: Run out of rooms! Remaining students not seated.'))
                break

            # Accessibility Warning
            if student.has_special_needs and not current_room.is_accessible:
                self.stdout.write(self.style.WARNING(f"Warning: Accessible room needed for {student}, but placed in {current_room}"))

            # Assign the seat
            seat_number = str(seats_filled_in_room + 1)
            SeatAssignment.objects.create(
                exam=exam,
                student=student,
                room=current_room,
                seat_number=seat_number
            )
            
            assigned_count += 1
            # self.stdout.write(f"Assigned {student} to {current_room} Seat {seat_number}")

            # Handle Room Capacity
            seats_filled_in_room += 1
            if seats_filled_in_room >= current_room.capacity:
                self.stdout.write(self.style.SUCCESS(f"Room {current_room} is full."))
                current_room = next(rooms_iter, None)
                seats_filled_in_room = 0

        self.stdout.write(self.style.SUCCESS(f'Allocation Complete! {assigned_count} students assigned.'))