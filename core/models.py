from django.db import models

class Student(models.Model):
    registration_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
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

class Course(models.Model):
    code = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.code} - {self.title}"

class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    duration_minutes = models.IntegerField()
    registered_students = models.ManyToManyField(Student, related_name='exams')

    def __str__(self):
        return f"{self.course.code} on {self.date_time.strftime('%Y-%m-%d %H:%M')}"

class SeatAssignment(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    seat_number = models.CharField(max_length=10)
    
    class Meta:
        unique_together = ('exam', 'student') 
        
    def __str__(self):
        return f"{self.student} -> {self.room} Seat {self.seat_number}"