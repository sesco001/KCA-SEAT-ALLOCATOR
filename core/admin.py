import csv
import io
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import admin
from django import forms
from django.contrib import messages
from django.http import HttpResponse
from .models import Student, Room, Course, Exam, SeatAssignment

# --- 1. THE IMPORT FORM ---
class CsvImportForm(forms.Form):
    csv_file = forms.FileField()

# --- 2. THE EXPORT FUNCTION (Keep your existing one) ---
def export_to_csv(modeladmin, request, queryset):
    meta = modeladmin.model._meta
    filename = f"{meta.verbose_name_plural}_export.csv"
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    writer = csv.writer(response)
    field_names = [field.name for field in meta.fields]
    writer.writerow(field_names)
    for obj in queryset:
        row = []
        for field in field_names:
            value = getattr(obj, field)
            if isinstance(value, bool): value = 'Yes' if value else 'No'
            row.append(str(value))
        writer.writerow(row)
    return response
export_to_csv.short_description = "📂 Export Selected to CSV"

# --- 3. THE ADVANCED STUDENT ADMIN ---
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'first_name', 'last_name', 'has_special_needs')
    search_fields = ('registration_number', 'first_name', 'last_name')
    list_filter = ('has_special_needs',)
    actions = [export_to_csv]
    
    # Point to our custom template with the button
    change_list_template = "admin/student_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            
            # Read the file
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            count = 0
            for row in reader:
                needs = True if row['special_needs'] == 'True' else False
                Student.objects.get_or_create(
                    registration_number=row['reg_no'],
                    defaults={
                        'first_name': row['first'],
                        'last_name': row['last'],
                        'email': row['email'],
                        'has_special_needs': needs
                    }
                )
                count += 1
            
            self.message_user(request, f"Successfully imported {count} students!")
            return redirect("..") # Go back to student list
        
        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "admin/csv_upload.html", payload)


# --- 4. OTHER ADMINS ---
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'is_accessible', 'capacity_status')
    actions = [export_to_csv]
    def capacity_status(self, obj): return f"{obj.capacity} Seats Max"

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('course', 'date_time', 'duration_minutes')
    actions = [export_to_csv]

@admin.register(SeatAssignment)
class SeatAssignmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'room', 'seat_number')
    list_filter = ('exam', 'room')
    actions = [export_to_csv]

admin.site.register(Course)
# --- 5. THE STAFF/ADMIN IMPORTER (New Section) ---
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

# Unregister the default User admin so we can use our own
admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Use our custom template with the Purple Button
    change_list_template = "admin/user_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            count = 0
            for row in reader:
                # Check if user already exists
                if not User.objects.filter(username=row['username']).exists():
                    # Create the user safely (Hashes the password)
                    user = User.objects.create_user(
                        username=row['username'],
                        email=row['email'],
                        password=row['password'],
                        first_name=row['first'],
                        last_name=row['last']
                    )
                    
                    # Set permissions
                    user.is_staff = True # All imported users can log in
                    if row['is_superuser'] == 'True':
                        user.is_superuser = True
                    
                    user.save()
                    count += 1
            
            self.message_user(request, f"Successfully imported {count} staff members!")
            return redirect("..")
        
        # Reuse the same upload form we made for Students
        form = CsvImportForm()
        payload = {"form": form}
        return render(request, "admin/csv_upload.html", payload)