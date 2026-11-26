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
    department = serializers.CharField(write_only=True, required=False)
    position = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'role', 'department', 'position', 'mobile_number'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        department = validated_data.pop('department', '')
        position = validated_data.pop('position', '')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data.get('role'),
            mobile_number=validated_data.get('mobile_number', ''),
        )

        user.set_password(password)
        user.save()

        user.registration_department = department
        user.registration_position = position

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
    user = serializers.StringRelatedField(read_only=True)
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


class EmployeeLeaveBalanceSerializer(serializers.ModelSerializer):
    # leave_type = LeaveTypeSerializer(read_only=True)
    leave_application = serializers.StringRelatedField(read_only=True)
    user = serializers.StringRelatedField(source='employee.user', read_only=True)
    available_balance = 'casual_leave_balance' + 'sick_leave_balance' + 'optional_leave_balance'
    class Meta:
        model = EmployeeLeaveBalance
        fields = '__all__'
        read_only_fields = ['leave_application', 'employee', 'user']

class LeaveApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = LeaveApplication
        fields = '__all__'
        read_only_fields = (
            'employee',
            'status',
            'manager_approved',
            'hr_approved',
            'applied_date'
        )

class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = '__all__'

    def get_details(self, obj):
        return {
            "date": obj.date,
        }
    



### Pageflow


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'role',
            'department',
            'first_name',
            'last_name',
            'date_joined',
            'is_active',
        ]
        read_only_fields = ['id', 'date_joined', 'is_active']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile (read-only for normal users)"""
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'role',
            'department',
            'first_name',
            'last_name',
            'date_joined',
        ]
        read_only_fields = ['id', 'username', 'email', 'role', 'date_joined']


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            'id',
            'unique_id',
            'title',
            'author',
            'category',
            'isbn',
            'publication_date',
            'total_copies',
            'available_copies',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['available_copies', 'created_at', 'updated_at']


class BookIssueSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_author = serializers.CharField(source='book.author', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = BookIssue
        fields = [
            'id',
            'book',
            'book_title',
            'book_author',
            'user',
            'username',
            'issue_date',
            'return_date',
            'status',
            'notes',
        ]
        read_only_fields = ['id', 'issue_date', 'book_title', 'book_author', 'username']

    def validate(self, attrs):
        book = attrs.get('book')
        user = self.context['request'].user

        # Check if book is available
        if book and book.available_copies <= 0:
            raise serializers.ValidationError({'book': 'This book currently has no available copies.'})

        # Check if user already has this book issued
        existing_issue = BookIssue.objects.filter(
            book=book,
            user=user,
            status='issued'
        ).exists()

        if existing_issue:
            raise serializers.ValidationError({'book': 'You already have this book issued.'})

        return attrs

    def create(self, validated_data):
        book = validated_data['book']
        user = self.context['request'].user

        # Decrease available copies
        book.available_copies = max(book.available_copies - 1, 0)
        book.save(update_fields=['available_copies'])

        validated_data.pop('user', None)

        # Create issue record
        return BookIssue.objects.create(user=user, **validated_data)


class BookReturnSerializer(serializers.Serializer):
    """Serializer for returning books"""
    issue_id = serializers.IntegerField()

    def validate_issue_id(self, value):
        try:
            issue = BookIssue.objects.get(
                id=value,
                user=self.context['request'].user,
                status='issued'
            )
            return issue
        except BookIssue.DoesNotExist:
            raise serializers.ValidationError("Invalid issue ID or book not currently issued to you.")

    def save(self):
        issue_obj = self.validated_data['issue_id']
        issue_obj.return_date = timezone.now()
        issue_obj.status = 'returned'
        issue_obj.save()

        # Increase available copies
        book = issue_obj.book
        book.available_copies += 1
        book.save(update_fields=['available_copies'])

        return issue_obj


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include username and password.')

class AdminReportSerializer(serializers.Serializer):
    """Serializer for admin reports"""
    total_books = serializers.IntegerField()
    total_users = serializers.IntegerField()
    total_issues = serializers.IntegerField()
    active_issues = serializers.IntegerField()
    total_available_copies = serializers.IntegerField()
    most_issued_books = BookSerializer(many=True)
    recent_issues = BookIssueSerializer(many=True)
