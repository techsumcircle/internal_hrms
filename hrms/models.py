from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings


# Create your models here.
class Role(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    password = models.CharField(max_length=128, null=True, blank=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.username
    
class EmailOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)

    def is_expired(self):
        return (timezone.now() - self.created_at).total_seconds() > 300  # 5 minutes
    
class MobileOTP(models.Model):
    mobile_number = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    
class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee', null=True, blank=True)
    employee_id = models.CharField(max_length=50, unique=True, null=True, blank=True, editable=False)
    full_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    marital_status = models.CharField(max_length=10, null=True, blank=True)
    blood_group = models.CharField(max_length=5, null=True, blank=True)
    position = models.CharField(max_length=50)
    department = models.CharField(max_length=50)
    date_of_joining = models.DateField(auto_now_add=True)
    mobile_number = models.CharField(max_length=15, null=True, blank=True)
    
    def __str__(self):
        return self.full_name
    
class EmployeeEmergencyContact(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    contact_name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=50)
    designation = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee} - {self.contact_name}"
    


class EmployeeAddressIdentity(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    identity_proof_type = models.CharField(max_length=100, null=True, blank=True)
    identity_proof_number = models.CharField(max_length=100, null=True, blank=True)
    identity_proof_document = models.FileField(upload_to='identity_proofs/', null=True, blank=True)
    identity_proof_type_2 = models.CharField(max_length=100, null=True, blank=True)
    identity_proof_number_2 = models.CharField(max_length=100, null=True, blank=True)
    identity_proof_document_2 = models.FileField(upload_to='identity_proofs/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} - {self.address_line1}"


class Attendance(models.Model):
    ATTENDENCE_STATUS = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Leave', 'Leave'),
        ('Work From Home', 'Work From Home'),
        ('Half Day', 'Half Day'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    check_in_time = models.TimeField(null=True, blank=True, default=timezone.now)
    check_out_time = models.TimeField(null=True, blank=True, default=timezone.now)
    total_duration = models.DurationField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ATTENDENCE_STATUS, default='Absent')
    class Meta:
        unique_together = ("employee", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.employee} - {self.date}"
    
class LeaveRequest(models.Model):
    LEAVE_CHOICES = [
        ('Applied', 'Applied'),
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    Attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True, default=timezone.now)
    end_date = models.DateField(null=True, blank=True, default=timezone.now)
    total_days = models.IntegerField(null=True, blank=True)
    reason = models.TextField(max_length=1000)
    applied_on = models.DateField(auto_now_add=True)
    half_day = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=LEAVE_CHOICES, default='Applied')
    manager_approval = models.BooleanField(default=False)
    hr_approval = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.employee} - {self.start_date} to {self.end_date}"


class LeaveType(models.Model):
    PAID_CHOICES = (
        ('PAID', 'Paid'),
        ('UNPAID', 'Unpaid'),
    )

    name = models.CharField(max_length=50)  # Casual, Sick, Optional Holiday
    paid_type = models.CharField(max_length=10, choices=PAID_CHOICES)
    half_day_allowed = models.BooleanField(default=False)
    probation_eligible = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
User = settings.AUTH_USER_MODEL

class EmployeeLeaveBalance(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    available_balance = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = ('employee', 'leave_type')

    def __str__(self):
        return f"{self.employee} - {self.leave_type}"
    
class LeaveApplication(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    )

    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_applications')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    total_days = models.DecimalField(max_digits=5, decimal_places=2)
    half_day = models.BooleanField(default=False)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    applied_date = models.DateTimeField(auto_now_add=True)

    # Approval Flow
    manager_approved = models.BooleanField(null=True, blank=True)
    hr_approved = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.status})"

# class Salary(models.Model):
#     employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
#     month = models.CharField(max_length=20)
#     year = models.DurationField()
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
#     net_pay = models.DecimalField(max_digits=10, decimal_places=2)
#     PF = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
#     tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

#     def __str__(self):
#         return f"{self.employee} - {self.month} {self.year}"
    
# class Holiday(models.Model):
#     LEAVE_CHOICES = [
#         ('Casual', 'Casual'),
#         ('Sick', 'Sick'),
#         ('Paid', 'Paid'),
#         ('Unpaid', 'Unpaid'),
#     ]
#     name = models.CharField(max_length=100)
#     leave_type = models.TextField(choices=LEAVE_CHOICES, default=True, max_length=20)
#     date = models.DateField(null=True, blank=True)

#     def __str__(self):
#         return f"{self.name} - {self.date}"
    
# class WorkFromHomeRequest(models.Model):
#     WFH_CHOICES = [
#         ('Regular', 'Regular'),
#         ('Pending', 'Pending'),
#         ('Approved', 'Approved'),
#         ('Rejected', 'Rejected'),
#     ]

#     employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
#     Applied_date = models.DateField()
#     from_date = models.DateField()
#     to_date = models.DateField()
#     total_days = models.IntegerField()
#     reason = models.TextField(max_length=1000)
#     status = models.CharField(max_length=20, choices=WFH_CHOICES, default='Regular')

#     def __str__(self):
#         return f"{self.employee} - {self.date}"
    
# class WorkFromHomeApproval(models.Model):
#     status_choices = [
#         ('pending', 'pending'),
#         ('approved', 'approved'),
#         ('rejected', 'rejected'),
#     ]
#     WorkFromHomeRequest = models.ForeignKey(WorkFromHomeRequest, on_delete=models.CASCADE)
#     manager_approval = models.BooleanField(default=False)
#     manager_approval_status = models.CharField(max_length=20, choices=status_choices, default='pending')
#     manager_approval_remarks = models.TextField(max_length=1000, null=True, blank=True)
#     manager_approval_date = models.DateField(auto_now_add=True)
#     hr_approval = models.BooleanField(default=False)
#     remarks = models.TextField(max_length=1000, null=True, blank=True)
#     date = models.DateField(auto_now_add=True)
#     def __str__(self):
#         return f"{self.WorkFromHomeRequest} - {self.status_choices}"
    
# class EmployeeEmergencyContact(models.Model):
#     employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
#     contact_name = models.CharField(max_length=100)
#     designation = models.CharField(max_length=50)
#     relationship = models.CharField(max_length=50)
#     persional_email = models.EmailField(unique=True)
#     office_email = models.EmailField(unique=True)
#     phone_number = models.CharField(max_length=15)
#     email = models.EmailField(null=True, blank=True)

#     def __str__(self):
#         return f"{self.employee} - {self.contact_name}"
    
# class EmployeeDocument(models.Model):
#     employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
#     document_name = models.CharField(max_length=100)
#     document_file = models.FileField(upload_to='employee_documents/')
#     upload_date = models.DateField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.employee} - {self.document_name}"
    
# class Attendance(models.Model):
#     ATTENDENCE_STATUS = [
#         ('Present', 'Present'),
#         ('Absent', 'Absent'),
#         ('Leave', 'Leave'),
#         ('Work From Home', 'Work From Home'),
#         ('Half Day', 'Half Day'),
#     ]
#     employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
#     date = models.DateField()
#     check_in_time = models.TimeField(null=True, blank=True, default=timezone.now)
#     check_out_time = models.TimeField(null=True, blank=True, default=timezone.now)
#     total_duration = models.DurationField(null=True, blank=True)
#     status = models.CharField(max_length=20, choices=ATTENDENCE_STATUS, default='Present')

#     def __str__(self):
#         return f"{self.employee} - {self.date}"
    
# class LeaveRequest(models.Model):
#     LEAVE_CHOICES = [
#         ('Applied', 'Applied'),
#         ('Pending', 'Pending'),
#         ('Approved', 'Approved'),
#         ('Rejected', 'Rejected'),
#     ]
#     employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
#     Attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, null=True, blank=True)
#     start_date = models.DateField(null=True, blank=True, default=timezone.now)
#     end_date = models.DateField(null=True, blank=True, default=timezone.now)
#     total_days = models.IntegerField(null=True, blank=True)
#     reason = models.TextField(max_length=1000)
#     applied_on = models.DateField(auto_now_add=True)
#     half_day = models.BooleanField(default=False)
#     status = models.CharField(max_length=20, choices=LEAVE_CHOICES, default='Applied')
#     manager_approval = models.BooleanField(default=False)
#     hr_approval = models.BooleanField(default=False)

#     def __str__(self):
#         return f"{self.employee} - {self.start_date} to {self.end_date}"

# class Salary(models.Model):
#     employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
#     month = models.CharField(max_length=20)
#     year = models.DurationField()
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
#     net_pay = models.DecimalField(max_digits=10, decimal_places=2)
#     PF = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
#     tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

#     def __str__(self):
#         return f"{self.employee} - {self.month} {self.year}"
    
# class Holiday(models.Model):
#     LEAVE_CHOICES = [
#         ('Casual', 'Casual'),
#         ('Sick', 'Sick'),
#         ('Paid', 'Paid'),
#         ('Unpaid', 'Unpaid'),
#     ]
#     name = models.CharField(max_length=100)
#     leave_type = models.TextField(choices=LEAVE_CHOICES, default=True, max_length=20)
#     date = models.DateField(null=True, blank=True)

#     def __str__(self):
#         return f"{self.name} - {self.date}"
    
# class WorkFromHomeRequest(models.Model):
#     WFH_CHOICES = [
#         ('Regular', 'Regular'),
#         ('Pending', 'Pending'),
#         ('Approved', 'Approved'),
#         ('Rejected', 'Rejected'),
#     ]

#     employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
#     Applied_date = models.DateField()
#     from_date = models.DateField()
#     to_date = models.DateField()
#     total_days = models.IntegerField()
#     reason = models.TextField(max_length=1000)
#     status = models.CharField(max_length=20, choices=WFH_CHOICES, default='Regular')

#     def __str__(self):
#         return f"{self.employee} - {self.date}"
    
# class WorkFromHomeApproval(models.Model):
#     status_choices = [
#         ('pending', 'pending'),
#         ('approved', 'approved'),
#         ('rejected', 'rejected'),
#     ]
#     WorkFromHomeRequest = models.ForeignKey(WorkFromHomeRequest, on_delete=models.CASCADE)
#     manager_approval = models.BooleanField(default=False)
#     manager_approval_status = models.CharField(max_length=20, choices=status_choices, default='pending')
#     manager_approval_remarks = models.TextField(max_length=1000, null=True, blank=True)
#     manager_approval_date = models.DateField(auto_now_add=True)
#     hr_approval = models.BooleanField(default=False)
#     remarks = models.TextField(max_length=1000, null=True, blank=True)
#     date = models.DateField(auto_now_add=True)
#     def __str__(self):
#         return f"{self.WorkFromHomeRequest} - {self.status_choices}"
    

