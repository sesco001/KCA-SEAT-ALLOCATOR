import csv
from django.core.management.base import BaseCommand
from core.models import Student

class Command(BaseCommand):
    help = 'Import students from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        file_path = options['file_path']

        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            count = 0
            for row in reader:
                # Convert 'True'/'False' string to Python Boolean
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

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} students!'))