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
    # password = serializers.CharField(write_only=True, min_length=6)

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

# class employeeOTPRegisterSerializerDemoNew(serializers.ModelSerializer):
    # status = serializers.ChoiceField(
    #     choices=Employee.STATUS_CHOICES,
    #     default='Pending',
    #     required=False
    # )
    # employee_kyc = serializers.ChoiceField(
    #     choices=Employee.KYC_CHOICES,
    #     default='Pending',
    #     required=False
    # )
    # wallet_balance = serializers.DecimalField(
    #     max_digits=12,
    #     decimal_places=2,
    #     default=0,
    #     required=False
    # )
    # employee_number = serializers.CharField(required=False)

    # class Meta:
    #     model = User
    #     fields = [
    #         'username', 'role',
    #         # 'status', 'employee_kyc',
    #         # 'wallet_balance', 'employee_number',
    #         'password'
    #     ]
    #     extra_kwargs = {
    #         'password': {'write_only': True, 'required': False}
    #     }

    # def create(self, validated_data):
    #     mobile_number = self.context.get('mobile_number')
    #     if not mobile_number:
    #         raise serializers.ValidationError("Mobile number missing")

        # status = validated_data.pop('status', 'Pending')
        # employee_kyc = validated_data.pop('employee_kyc', 'Pending')
        # wallet_balance = validated_data.pop('wallet_balance', 0)
        # employee_number = validated_data.pop('employee_number')

        # password = validated_data.pop('password', '123456')
        # validated_data['password'] = make_password(password)

        # user = User.objects.create(**validated_data)

        # Employee.objects.create(
        #     user=user,
        #     mobile_number=mobile_number,
        #     employee_number=employee_number
        # )

        # return user
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
    employee = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())
    class Meta:
        model = EmployeeEmergencyContact
        fields = '__all__'

class EmployeeAddressIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeAddressIdentity
        fields = '__all__'

class AttendanceSerializer(serializers.ModelSerializer):
    employee = serializers.StringRelatedField(read_only=True)
    total_duration = serializers.DurationField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Attendance
        fields = "__all__"

class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = '__all__'


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'

class EmployeeLeaveBalanceSerializer(serializers.ModelSerializer):
    leave_type = LeaveTypeSerializer(read_only=True)

    class Meta:
        model = EmployeeLeaveBalance
        fields = '__all__'

class LeaveApplicationSerializer(serializers.ModelSerializer):
    employee = serializers.ReadOnlyField(source='employee.id')

    class Meta:
        model = LeaveApplication
        fields = '__all__'
        read_only_fields = ('status', 'manager_approved', 'hr_approved', 'applied_date')

# class SalarySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Salary
#         fields = '__all__'

# class HolidaySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Holiday
#         fields = '__all__'

# class WorkFromHomeRequestSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = WorkFromHomeRequest
#         fields = '__all__'

# class WorkFromHomeApprovalSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = WorkFromHomeApproval
#         fields = '__all__'