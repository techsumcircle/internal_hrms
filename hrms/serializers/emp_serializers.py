from django.contrib.auth.models import User
from hrms.models import *
from rest_framework import serializers
from django.utils.crypto import get_random_string
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password, check_password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
    

class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'password', 'role', 'mobile_number'
        ]
        
    def create(self, validated_data):
        password = get_random_string(12)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data.get('role', ''),
            mobile_number=validated_data.get('mobile_number', ''),
        )
        user.set_password(password)  # hashes password
        user.raw_password = password
        user.save()    
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            username=data['username'],
            password=data['password']
        )
        if not user:
            raise serializers.ValidationError("Invalid username or password")
        data['user'] = user
        return data
    
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.CharField()
    mobile_number = serializers.CharField(read_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
        
class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'

class EmployeeEmergencyContactSerializer(serializers.ModelSerializer):
    employee = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = EmployeeEmergencyContact
        fields = '__all__'

class EmployeeAddressIdentitySerializer(serializers.ModelSerializer):
    employee = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = EmployeeAddressIdentity
        fields = '__all__'

class EmployeeDetailesCheckBoxSerializer(serializers.ModelSerializer):
    details = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeDetailesCheckBox
        fields = "__all__"
        extra_kwargs = {
            "employee": {"read_only": True}
        }

    def get_details(self, obj):
        return {
            "employee": EmployeeSerializer(obj.employee).data,
            "emergency_contact": EmployeeEmergencyContactSerializer(EmployeeEmergencyContact.objects.filter(employee=obj.employee).first()).data,
            "address_identity": EmployeeAddressIdentitySerializer(EmployeeAddressIdentity.objects.filter(employee=obj.employee).first()).data,
        }


class AttendanceSerializer(serializers.ModelSerializer):
    employee = serializers.StringRelatedField(read_only=True)
    total_duration = serializers.DurationField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Attendance
        fields = "__all__"

class WorkFromHomeRequestSerializer(serializers.ModelSerializer):
    employee = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = WorkFromHomeRequest
        fields = '__all__'
        read_only_fields = ["employee", "total_days", "status"]

class WorkFromHomeApprovalSerializer(serializers.ModelSerializer):
    wfh_request = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = WorkFromHomeApproval
        fields = '__all__'
        fields = [
            "id",
            "wfh_request",
            "status",
            "remarks",
            "approved_date"
        ]
        read_only_fields = ["approved_date"]

# class LeaveRequestSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = LeaveApplication
#         fields = '__all__'


class LeaveTypeSerializer(serializers.ModelSerializer):
    # employee = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = LeaveType
        fields = '__all__'
        # read_only_fields = ["employee"]

class EmployeeLeaveBalanceSerializer(serializers.ModelSerializer):
    # leave_type = LeaveTypeSerializer(read_only=True)
    leave_application = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = EmployeeLeaveBalance
        fields = '__all__'
        read_only_fields = ['leave_application']


# class LeaveApprovalSerializer(serializers.ModelSerializer):
#     leave_application = serializers.StringRelatedField(read_only=True)
#     class Meta:
#         model = LeaveApplication
#         fields = [
#             "id",
#             "leave_application",
#             "status",
#             "admin_approved",
#             "hr_approved"
#         ]
#         read_only_fields = ['admin_approved', 'hr_approved']


# def deduct_leave_balance(sender, instance, created, **kwargs):

#     # sirf APPROVAL pe chale
#     if instance.status != 'APPROVED':
#         return

#     with transaction.atomic():

#         balance = EmployeeLeaveBalance.objects.select_for_update().get(
#             employee=instance.employee,
#             leave_type=instance.leave_type
#         )

#         days = instance.total_days

#         if instance.leave_type.leave_type == 'Casual':
#             if balance.casual_leave_balance < days:
#                 raise ValueError("Insufficient Casual Leave")

#             balance.casual_leave_balance -= days

#         elif instance.leave_type.leave_type == 'Sick':
#             if balance.sick_leave_balance < days:
#                 raise ValueError("Insufficient Sick Leave")

#             balance.sick_leave_balance -= days

#         elif instance.leave_type.leave_type == 'Optional':
#             if balance.optional_leave_balance < days:
#                 raise ValueError("Insufficient Optional Leave")

#             balance.optional_leave_balance -= days

#         # total available balance
#         if balance.available_balance < days:
#             raise ValueError("Insufficient Total Leave Balance")

#         balance.available_balance -= days
#         balance.save()



# Employee Apply
#    ↓
# Validation (Balance + Overlap + Half Day)
#    ↓
# Status = PENDING
#    ↓
# admin Approves
#    ↓
# HR Approves
#    ↓
# Leave Approved
#    ↓
# Leave Balance Deducted


class LeaveApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = LeaveApplication
        fields = '__all__'
        read_only_fields = (
            'employee',
            'status',
            'admin_approved',
            'hr_approved',
            'applied_date'
        )

    # def validate(self, attrs):
    #     employee = self.context['request'].user
    #     leave_type = attrs['leave_type']
    #     days = attrs['total_days']
    #     half_day = attrs.get('half_day', False)
    #     from_date = attrs['from_date']
    #     to_date = attrs['to_date']

    #     # Date validation
    #     if from_date > to_date:
    #         raise serializers.ValidationError("Invalid date range")

    #     # Half day rule
    #     if half_day and not leave_type.half_day_allowed:
    #         raise serializers.ValidationError("Half-day not allowed")

    #     # Overlap check
    #     if LeaveApplication.objects.filter(
    #         employee=Employee.objects.get(user=employee),
    #         from_date__lte=to_date,
    #         to_date__gte=from_date,
    #         status__in=['PENDING', 'APPROVED']
    #     ).exists():
    #         raise serializers.ValidationError("Leave already applied")

    #     balance = EmployeeLeaveBalance.objects.get(employee=Employee.objects.get(user=employee))

    #     # Balance validation
    #     if leave_type.leave_type == 'Casual' and balance.casual_leave_balance < days:
    #         raise serializers.ValidationError("Insufficient Casual Leave")

    #     if leave_type.leave_type == 'Sick' and balance.sick_leave_balance < days:
    #         raise serializers.ValidationError("Insufficient Sick Leave")

    #     if leave_type.leave_type == 'Optional' and balance.optional_leave_balance < days:
    #         raise serializers.ValidationError("Insufficient Optional Leave")

    #     if leave_type.leave_type == 'CompOff' and balance.compoff_balance < days:
    #         raise serializers.ValidationError("Insufficient Comp-Off balance")

    #     if balance.available_balance < days:
    #         raise serializers.ValidationError("Insufficient total balance")

    #     return attrs
