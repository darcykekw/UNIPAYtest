from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from random import randint, choice
from datetime import timedelta
import hashlib
import hmac
from django.conf import settings

from paymentorg.models import (
    Organization,
    Officer,
    Student,
    FeeType,
    PaymentRequest,
    Course,
    College,
)


class Command(BaseCommand):
    help = "Create fake development data for UniPay (organizations, officers, students, fees, requests)."

    def add_arguments(self, parser):
        parser.add_argument("--students", type=int, default=10, help="Number of students to create (default: 10)")
        parser.add_argument("--orgs", type=int, default=2, help="Number of organizations to create (default: 2)")
        parser.add_argument("--fees", type=int, default=3, help="Fee types per org (default: 3)")
        parser.add_argument("--requests", type=int, default=1, help="Payment requests per student (default: 1)")

    def handle(self, *args, **options):
        num_students = options["students"]
        num_orgs = options["orgs"]
        fees_per_org = options["fees"]
        requests_per_student = options["requests"]

        self.stdout.write(self.style.MIGRATE_HEADING("Creating organizations"))
        requested_orgs = [
            ("BIO", "Bachelor of Science in Biology"),
            ("MBIO", "Bachelor of Science in Marine Biology"),
            ("BSCS", "Bachelor of Science in Computer Science"),
            ("BSES", "Bachelor of Science in Environmental Science"),
            ("BSIT", "Bachelor of Science in Information Technology"),
            ("STUDORG", "Student organizations"),
        ]
        orgs = []
        for code, name in requested_orgs:
            org, _ = Organization.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "department": name,
                    "description": "Seeded organization",
                    "contact_email": f"{code.lower()}@example.com",
                    "contact_phone": "0917-000-0000",
                    "booth_location": "Main Building",
                },
            )
            orgs.append(org)
        self.stdout.write(self.style.SUCCESS(f"Organizations: {len(orgs)}"))

        self.stdout.write(self.style.MIGRATE_HEADING("Creating colleges/departments"))
        colleges_data = [
            ("College of Sciences", "COS"),
            ("College of Engineering", "COE"),
            ("College of Arts and Letters", "CAL"),
            ("College of Business Administration", "CBA"),
        ]
        colleges = []
        for name, code in colleges_data:
            college, _ = College.objects.get_or_create(
                name=name,
                defaults={"code": code, "description": f"Seeded {name}"}
            )
            colleges.append(college)
        self.stdout.write(self.style.SUCCESS(f"Colleges: {len(colleges)}"))

        self.stdout.write(self.style.MIGRATE_HEADING("Creating courses/programs"))
        courses_data = [
            ("Bachelor of Science in Biology", "BSBIO", colleges[0]),
            ("Bachelor of Science in Marine Biology", "BSMBIO", colleges[0]),
            ("Bachelor of Science in Computer Science", "BSCS", colleges[0]),
            ("Bachelor of Science in Environmental Science", "BSES", colleges[0]),
            ("Bachelor of Science in Information Technology", "BSIT", colleges[0]),
            ("Bachelor of Science in Chemistry", "BSCHEM", colleges[0]),
            ("Bachelor of Science in Mathematics", "BSMATH", colleges[0]),
            ("Bachelor of Science in Civil Engineering", "BSCE", colleges[1]),
            ("Bachelor of Science in Electrical Engineering", "BSEE", colleges[1]),
            ("Bachelor of Arts in English", "BAENG", colleges[2]),
            ("Bachelor of Science in Business Administration", "BSBA", colleges[3]),
        ]
        courses = []
        for name, code, college in courses_data:
            course, _ = Course.objects.get_or_create(
                name=name,
                college=college,
                defaults={"code": code, "description": f"Seeded {name}"}
            )
            courses.append(course)
        self.stdout.write(self.style.SUCCESS(f"Courses: {len(courses)}"))

        self.stdout.write(self.style.MIGRATE_HEADING("Creating officers (staff users)"))
        for org in orgs:
            username = f"officer_{org.code.lower()}"
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "first_name": "Org",
                    "last_name": org.code,
                    "is_staff": True,
                },
            )
            user.set_password("admin123")
            user.save()
            Officer.objects.get_or_create(
                user=user,
                defaults={
                    "employee_id": f"EMP-{org.code}",
                    "first_name": "Org",
                    "last_name": org.code,
                    "email": user.email,
                    "phone_number": "0917-123-4567",
                    "organization": org,
                    "role": "Treasurer",
                    "can_process_payments": True,
                },
            )
        self.stdout.write(self.style.SUCCESS("Officers created."))

        # Superusers for quick access (student and officer variants)
        self.stdout.write(self.style.MIGRATE_HEADING("Creating superusers (for testing)"))
        # super officer
        if orgs:
            su_officer, created = User.objects.get_or_create(
                username="superofficer",
                defaults={
                    "email": "superofficer@example.com",
                    "first_name": "Super",
                    "last_name": "Officer",
                    "is_staff": True,
                    "is_superuser": True,
                },
            )
            if created:
                su_officer.set_password("admin123")
                su_officer.save()
                Officer.objects.get_or_create(
                    user=su_officer,
                    defaults={
                        "employee_id": "EMP-SUPER",
                        "first_name": "Super",
                        "last_name": "Officer",
                        "email": su_officer.email,
                        "phone_number": "0917-111-1111",
                        "organization": orgs[0],
                        "role": "Administrator",
                        "can_process_payments": True,
                        "can_void_payments": True,
                        "can_generate_reports": True,
                    },
                )
        # super student
        su_student, created = User.objects.get_or_create(
            username="superstudent",
            defaults={
                "email": "superstudent@example.com",
                "first_name": "Super",
                "last_name": "Student",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            su_student.set_password("admin123")
            su_student.save()
            # Use first available course and college
            default_course = courses[0] if courses else None
            default_college = colleges[0] if colleges else None
            if default_course and default_college:
                Student.objects.get_or_create(
                    user=su_student,
                    defaults={
                        "student_id_number": "2025-ADMIN",
                        "first_name": su_student.first_name,
                        "last_name": su_student.last_name,
                        "middle_name": "X",
                        "email": su_student.email,
                        "phone_number": "0917-222-2222",
                        "course": default_course,
                        "year_level": 4,
                        "college": default_college,
                        "academic_year": "2024-2025",
                        "semester": "1st Semester",
                    },
                )
        self.stdout.write(self.style.SUCCESS("Superusers ensured (user/pass: superofficer admin123, superstudent admin123)."))

        self.stdout.write(self.style.MIGRATE_HEADING("Creating fee types"))
        fees = []
        for org in orgs:
            for i in range(fees_per_org):
                fee, _ = FeeType.objects.get_or_create(
                    organization=org,
                    name=f"Fee {i+1}",
                    academic_year="2024-2025",
                    semester="1st Semester",
                    defaults={
                        "amount": Decimal(str(100 + 50 * (i + 1))),
                        "description": "Sample fee",
                        "applicable_year_levels": "All",
                    },
                )
                fees.append(fee)
        self.stdout.write(self.style.SUCCESS(f"Fee types: {len(fees)}"))

        self.stdout.write(self.style.MIGRATE_HEADING("Creating students"))
        students = []
        for i in range(num_students):
            username = f"student{i+1:03d}"
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "first_name": f"Student{i+1}",
                    "last_name": "Test",
                },
            )
            user.set_password("password123")
            user.save()
            # Randomly assign course and college
            selected_course = choice(courses) if courses else None
            selected_college = selected_course.college if selected_course else (colleges[0] if colleges else None)
            if selected_course and selected_college:
                stu, _ = Student.objects.get_or_create(
                    user=user,
                    defaults={
                        "student_id_number": f"2025-{10000+i}",
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "middle_name": "A",
                        "email": user.email,
                        "phone_number": "0917-000-0000",
                        "course": selected_course,
                        "year_level": randint(1, 4),
                        "college": selected_college,
                        "academic_year": "2024-2025",
                        "semester": "1st Semester",
                    },
                )
                students.append(stu)
        self.stdout.write(self.style.SUCCESS(f"Students: {len(students)}"))

        self.stdout.write(self.style.MIGRATE_HEADING("Creating payment requests"))
        count_requests = 0
        for stu in students:
            for _ in range(requests_per_student):
                fee = choice(fees)
                pr, created = PaymentRequest.objects.get_or_create(
                    student=stu,
                    organization=fee.organization,
                    fee_type=fee,
                    amount=fee.amount,
                    queue_number=f"{fee.organization.code}-{randint(1,999):03d}",
                    defaults={
                        "payment_method": "CASH",
                        "status": "PENDING",
                        "qr_signature": "",
                        "expires_at": timezone.now() + timedelta(minutes=30),
                    },
                )
                if created:
                    count_requests += 1
                # ensure qr signature exists
                if not pr.qr_signature:
                    secret = getattr(settings, 'SECRET_KEY', 'default-insecure-key').encode('utf-8')
                    message = str(pr.request_id).encode('utf-8')
                    pr.qr_signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
                    pr.save(update_fields=["qr_signature"])
        self.stdout.write(self.style.SUCCESS(f"Payment requests created: {count_requests}"))

        self.stdout.write(self.style.SUCCESS("Fake data generation complete."))
