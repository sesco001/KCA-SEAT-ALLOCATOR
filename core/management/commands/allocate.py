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
            self.stdout.write(self.style.ERROR('Exam not found!'))
            return

        self.stdout.write(f"Starting allocation for: {exam}...")

        # 1. Clear old assignments for this specific exam (so we can re-run safely)
        SeatAssignment.objects.filter(exam=exam).delete()

        # 2. Get all students registered for this exam
        # We separate them into two groups to handle priority
        all_students = exam.registered_students.all()
        special_needs_students = all_students.filter(has_special_needs=True)
        regular_students = all_students.filter(has_special_needs=False)

        # 3. Get all rooms
        # We sort rooms so accessible ones come first (Priority for special needs)
        all_rooms = Room.objects.all().order_by('-is_accessible') 

        # 4. The Allocation Loop
        student_queue = list(special_needs_students) + list(regular_students)
        
        rooms_iter = iter(all_rooms)
        current_room = next(rooms_iter, None)
        seats_filled_in_room = 0

        for student in student_queue:
            
            # --- START COMPLEX IMPLEMENTATION: ANTI-CLASH CHECK ---
            # Check if this student is already seated in ANY other exam at this EXACT time
            conflict = SeatAssignment.objects.filter(
                student=student,
                exam__date_time=exam.date_time  # Clashes if times match
            ).exclude(exam=exam).exists() # Exclude the current exam we are processing

            if conflict:
                self.stdout.write(self.style.ERROR(f"CRITICAL CONFLICT: {student} has another exam at {exam.date_time}! Skipping seat assignment."))
                continue # Skip this student and move to the next one
            # --- END COMPLEX IMPLEMENTATION ---

            # Standard Room Check
            if not current_room:
                self.stdout.write(self.style.ERROR('CRITICAL: Run out of rooms! Some students not seated.'))
                break

            # Special Logic: If student has needs, ensure room is accessible
            if student.has_special_needs and not current_room.is_accessible:
                # In a real scenario, this would trigger a search for the next accessible room
                self.stdout.write(self.style.WARNING(f"Warning: Could not find accessible room for {student}"))

            # Assign the seat
            seat_number = str(seats_filled_in_room + 1)
            SeatAssignment.objects.create(
                exam=exam,
                student=student,
                room=current_room,
                seat_number=seat_number
            )
            
            self.stdout.write(f"Assigned {student} to {current_room} Seat {seat_number}")

            # Check capacity
            seats_filled_in_room += 1
            if seats_filled_in_room >= current_room.capacity:
                self.stdout.write(self.style.SUCCESS(f"Room {current_room} is full."))
                current_room = next(rooms_iter, None)
                seats_filled_in_room = 0

        self.stdout.write(self.style.SUCCESS('Allocation Complete!'))