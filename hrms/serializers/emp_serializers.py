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


# class LeaveTypeSerializer(serializers.ModelSerializer):
#     # employee = serializers.StringRelatedField(read_only=True)
#     class Meta:
#         model = LeaveType
#         fields = '__all__'
#         # read_only_fields = ["employee"]

# class EmployeeLeaveBalanceSerializer(serializers.ModelSerializer):
#     leave_type = LeaveTypeSerializer(read_only=True)

#     class Meta:
#         model = EmployeeLeaveBalance
#         fields = '__all__'

# class LeaveApplicationSerializer(serializers.ModelSerializer):
#     employee = serializers.StringRelatedField(read_only=True)
#     leave_type = serializers.StringRelatedField(read_only=True)

#     class Meta:
#         model = LeaveApplication
#         fields = '__all__'
#         read_only_fields = ("employee",'status', 'manager_approved', 'hr_approved', 'applied_date')

