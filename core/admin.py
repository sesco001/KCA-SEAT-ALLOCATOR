import csv
from django.http import HttpResponse
from django.contrib import admin
from django import forms
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.core.management import call_command # <--- Magic tool to run commands
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
import io

from .models import Student, Room, Course, Exam, SeatAssignment

# --- 1. THE EXPORT ENGINE ---
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

# --- 2. THE ALLOCATION ENGINE (NEW) ---
@admin.action(description='⚡ Allocate Seats for Selected Exams')
def run_allocation(modeladmin, request, queryset):
    for exam in queryset:
        try:
            # This runs "python manage.py allocate <exam_id>" internally
            call_command('allocate', exam_id=exam.id)
            modeladmin.message_user(request, f"Successfully allocated seats for {exam}.", messages.SUCCESS)
        except Exception as e:
            modeladmin.message_user(request, f"Error allocating {exam}: {str(e)}", messages.ERROR)

# --- 3. CSV IMPORT FORM ---
class CsvImportForm(forms.Form):
    csv_file = forms.FileField()

# --- 4. ADMIN CLASSES ---

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'first_name', 'last_name', 'has_special_needs')
    search_fields = ('registration_number', 'first_name', 'last_name')
    list_filter = ('has_special_needs',)
    actions = [export_to_csv]
    change_list_template = "admin/student_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [path('import-csv/', self.import_csv),]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            count = 0
            for row in reader:
                needs = True if row['special_needs'] == 'True' else False
                Student.objects.get_or_create(
                    registration_number=row['reg_no'],
                    defaults={'first_name': row['first'], 'last_name': row['last'], 'email': row['email'], 'has_special_needs': needs}
                )
                count += 1
            self.message_user(request, f"Successfully imported {count} students!")
            return redirect("..")
        form = CsvImportForm()
        return render(request, "admin/csv_upload.html", {"form": form})

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'is_accessible', 'capacity_status')
    actions = [export_to_csv]
    def capacity_status(self, obj): return f"{obj.capacity} Seats Max"

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('course', 'date_time', 'duration_minutes')
    # Add the NEW Allocation Button here
    actions = [export_to_csv, run_allocation] 

@admin.register(SeatAssignment)
class SeatAssignmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'room', 'seat_number')
    list_filter = ('exam', 'room')
    actions = [export_to_csv]

admin.site.register(Course)

# --- 5. USER ADMIN HACK (Keep your import logic) ---
admin.site.unregister(User)
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    change_list_template = "admin/user_changelist.html"
    def get_urls(self):
        return [path('import-csv/', self.import_csv)] + super().get_urls()
    
    def import_csv(self, request):
        # ... (Your existing user import logic goes here or keeps working if you paste it fully)
        # For brevity, assuming you keep the logic we wrote previously.
        pass
