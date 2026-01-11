from django.db import models

class Course(models.Model):
    # I changed 'title' to 'name' so it works with your templates ({{ course.name }})
    code = models.CharField(max_length=20, unique=True) # e.g. "BIT 111"
    name = models.CharField(max_length=100)             # e.g. "Intro to Programming"

    def __str__(self):
        return f"{self.code} - {self.name}"

class Student(models.Model):
    registration_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    
    # --- 1. PORTAL ACCESS ---
    # Password for students to log in and register units
    password = models.CharField(max_length=100, default="student123")
    
    # --- 2. UNIT REGISTRATION (The "Real University" Logic) ---
    # This links the student to the subjects they are taking this semester.
    # The Allocator will strictly look at this list.
    enrolled_courses = models.ManyToManyField(Course, related_name='students', blank=True)

    # --- 3. ACCESSIBILITY ---
    has_special_needs = models.BooleanField(default=False) 
    special_needs_details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.registration_number} - {self.first_name}"

class Room(models.Model):
    name = models.CharField(max_length=20)
    capacity = models.IntegerField()
    is_accessible = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} (Cap: {self.capacity})"

class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    duration_minutes = models.IntegerField()
    
    # Note: We removed 'registered_students' from here.
    # Why? Because we now use the 'enrolled_courses' on the Student model.
    # This is smarter: If a student is in the Course, they are automatically in the Exam.

    def __str__(self):
        return f"{self.course.code} Exam on {self.date_time.strftime('%Y-%m-%d %H:%M')}"

class SeatAssignment(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    seat_number = models.CharField(max_length=10) # Using CharField allows "A1" or "10"
    
    class Meta:
        unique_together = ('exam', 'student') # A student cannot have two seats for the same exam
        
    def __str__(self):
        return f"{self.student} -> {self.room} Seat {self.seat_number}"