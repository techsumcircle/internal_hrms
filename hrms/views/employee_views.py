from datetime import timedelta, datetime, time
from django.utils import timezone
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import random
import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Sum
from hrms.models import Role, MobileOTP, EmailOTP, Employee, User, Book, BookIssue
from rest_framework.permissions import IsAuthenticated, AllowAny
from hrms.serializers.emp_serializers import *
from rest_framework_simplejwt.tokens import RefreshToken 
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import get_object_or_404
from django.contrib.postgres.search import SearchVector
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction



class RoleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            role = Role.objects.filter(status=True)
            serializer = RoleSerializer(role, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request):
        try:
            user = request.user
            if user.role.name not in ["HR", "MANAGER"]:
                return Response({'error': 'You are not authorized to create roles'}, status=status.HTTP_403_FORBIDDEN)
            serializer = RoleSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request, pk):
        try:
            user = request.user
            if user.role.name not in ["HR", "MANAGER"]:
                return Response({'error': 'You are not authorized to update roles'}, status=status.HTTP_403_FORBIDDEN)
            try:
                role = Role.objects.get(pk=pk, status=True)
            except Role.DoesNotExist:
                return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)
            serializer = RoleSerializer(role, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Role.DoesNotExist:
            return Response({'error': 'Role does not Exists'}, status=status.HTTP_404_NOT_FOUND)
        
        
    def delete(self, request, pk):
        try:
            user = request.user
            if user.role.name not in ["HR", "MANAGER"]:
                return Response({'error': 'You are not authorized to delete roles'}, status=status.HTTP_403_FORBIDDEN)
            try:
                role = Role.objects.get(pk=pk)
            except Role.DoesNotExist:
                return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)
            if role.status == False:
                return Response({'error': f'{role.name} Role is already deleted'}, status=status.HTTP_400_BAD_REQUEST)
            role.status = False
            role.save()
            return Response({'message': 'Role deleted successfully'}, status=status.HTTP_200_OK)
        except Role.DoesNotExist:
            return Response({'error': 'Role does not Exists'}, status=status.HTTP_404_NOT_FOUND)


class RegisterAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            if user.role and user.role.name  not in ['HR', 'MANAGER']:
                   return Response({'error': 'Kindly contact with Administrator for the registration process.'}, status=status.HTTP_400_BAD_REQUEST)

            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():

                email_id = serializer.validated_data.get('email')
                email = User.objects.annotate(search=SearchVector('email')).filter(search=email_id)

                if email.exists() and email.first().email == email_id:
                    return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
                
                # return Response({'error': serializer.data}, status=status.HTTP_400_BAD_REQUEST)
                user = serializer.save()               
                if user.role and user.role.name == 'EMPLOYEE': 
                    employee_num = Employee.objects.order_by('-id').first()        
                    if employee_num and employee_num.employee_id:
                        try:
                            last_transaction = int(employee_num.employee_id.replace('EMP', ''))
                            employee_id = f"EMP{last_transaction + 1:03d}"
                        except:
                            employee_id = "EMP001"
                    else:
                        employee_id = "EMP001"

                    # available_balance = 
                    # print(user.id)
                    Employee.objects.create(
                        user=user,
                        employee_id=employee_id,
                        full_name=user.get_full_name()or user.username,
                        email=user.email,
                        mobile_number=user.mobile_number,
                        )
                    
                    EmployeeLeaveBalance.objects.create(
                        employee=employee_num,
                        )
                return Response(
                    {
                        "message": "User registered successfully",
                        "user_id": user.id,
                        "employee_id": user.employee.employee_id if hasattr(user, 'employee') else None,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "mobile_number": user.mobile_number,
                        "email": user.email,
                        "password": user.raw_password,
                        "role": user.role.name if user.role else None
                    }, status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            # username = request.data.get('username')
            # user = User.objects.get(username=username)

            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
    
            return Response(
                {
                    "message": "Login successful",
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email
                    }
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            if request.user.role and request.user.role.name not in ['HR', 'MANAGER']:
                   return Response({'error': 'You do not have permission to view all users.'}, status=status.HTTP_403_FORBIDDEN)
            user = User.objects.all()
            serializer = UserSerializer(user, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LoginWithOTPApiView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            mobile_number = request.data.get('mobile_number')
            email_id = request.data.get('email_id')
            if not mobile_number:
                return Response({'error': 'Mobile number is required'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(mobile_number=mobile_number)
            except User.DoesNotExist:
                return Response({'error': 'User with this mobile number does not exist'}, status=status.HTTP_404_NOT_FOUND)

            otp = str(random.randint(100000, 999999))
            MobileOTP.objects.create(mobile_number=mobile_number, otp=otp, created_at=datetime.now())

            sms_message = f"Your OTP for login is {otp}. Valid for 10 mins. SumCircle"
            params = {
                "usersName": settings.VASBAY_USERNAME,
                "key": settings.VASBAY_API_KEY,
                "route": 2,
                "message": sms_message,
                "numbers": mobile_number,
                "senderId": settings.VASBAY_SENDER_ID,
                "entityId": settings.VASBAY_ENTITY_ID,
                "contentId": settings.VASBAY_CONTENT_ID
            }
            response = requests.get(settings.VASBAY_API_URL, params=params, timeout=10)
            data = response.json()
            sms_status = ""
            msg = data.get("msg")
            if isinstance(msg, dict):
                response_block = msg.get("response")
                if isinstance(response_block, dict):
                    sms_status = response_block.get("0", {}).get("status", "")
            elif isinstance(msg, str):
                sms_status = msg

            if sms_status in ["Sent", "Delivered"]:
                return Response({"message": "OTP sent to mobile."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Failed to send OTP.", "status": sms_status}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ForgetPasswordView(APIView):
    """
    Unified forget password API
    Steps:
    1. Send OTP to email or mobile.
    2. Verify OTP.
    3. Reset password.
    """

    def post(self, request):
        email_id = request.data.get("email_id")  
        mobile_number = request.data.get("mobile_number")
        # print(email_id, mobile_number)

        if not email_id and not mobile_number:
            return Response({"error": "Either email_id or mobile_number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if email_id:
            method = "email"
        elif mobile_number:
            method = "mobile"
            
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        email = User.objects.annotate(search=SearchVector('email')).filter(search=email_id)
        mobile = User.objects.annotate(search=SearchVector('mobile_number')).filter(search=mobile_number)

        # Step 1: Generate & send OTP
        if not otp:
            generated_otp = str(random.randint(100000, 999999))

            if method == "email":
                # Remove previous OTP
                EmailOTP.objects.filter(email=email_id).delete()
                # Save OTP
                EmailOTP.objects.create(email=email_id, otp=generated_otp, created_at=datetime.now())

                # Send email
                subject = "Your OTP for Password Reset"
                message = f"Your OTP is {generated_otp}. It is valid for 10 minutes."
                try:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email_id])
                    return Response({"message": "OTP sent to email."}, status=status.HTTP_200_OK)
                except Exception as e:
                    return Response({"error": "Failed to send email.", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            elif method == "mobile":
                # Remove previous OTP
                MobileOTP.objects.filter(mobile_number=mobile_number).delete()
                # Save OTP
                MobileOTP.objects.create(mobile_number=mobile_number, otp=generated_otp, created_at=datetime.now())

                # Send SMS via Vasbay
                sms_message = f"Your OTP is {generated_otp}. Valid for 10 mins. SumCircle"
                params = {
                    "usersName": settings.VASBAY_USERNAME,
                    "key": settings.VASBAY_API_KEY,
                    "route": 2,
                    "message": sms_message,
                    "numbers": mobile_number,
                    "senderId": settings.VASBAY_SENDER_ID,
                    "entityId": settings.VASBAY_ENTITY_ID,
                    "contentId": settings.VASBAY_CONTENT_ID
                }
                try:
                    response = requests.get(settings.VASBAY_API_URL, params=params, timeout=10)
                    data = response.json()
                    sms_status = ""
                    msg = data.get("msg")
                    if isinstance(msg, dict):
                        response_block = msg.get("response")
                        if isinstance(response_block, dict):
                            sms_status = response_block.get("0", {}).get("status", "")
                    elif isinstance(msg, str):
                        sms_status = msg

                    if sms_status in ["Sent", "Delivered"]:
                        return Response({"message": "OTP sent to mobile."}, status=status.HTTP_200_OK)
                    else:
                        return Response({"error": "OTP not delivered.", "status": sms_status}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                except Exception as e:
                    return Response({"error": "Failed to send OTP.", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"error": "Invalid method. Use 'email' or 'mobile'."}, status=status.HTTP_400_BAD_REQUEST)

        # Step 2: OTP verify + reset password
        if otp:
            if not new_password or not confirm_password:
                return Response({"message": "OTP verified. Now provide new_password and confirm_password."}, status=status.HTTP_200_OK)

            if new_password != confirm_password:
                return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

            # Verify OTP
            otp_obj = None
            try:
                if method == "email":
                    otp_obj = EmailOTP.objects.get(email=email_id)
                else:
                    otp_obj = MobileOTP.objects.get(mobile_number=mobile_number)
            except (EmailOTP.DoesNotExist, MobileOTP.DoesNotExist):
                return Response({"error": "OTP not found."}, status=status.HTTP_400_BAD_REQUEST)

            # Check expiry
            if timezone.now() > otp_obj.created_at + timedelta(minutes=10):
                return Response({"error": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST)

            if otp_obj.otp != otp:
                return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

            # Update password
            try:
                if method == "email":
                    user = User.objects.get(email=email_id)
                else:
                    user = User.objects.get(mobile_number=mobile_number)
                user.password = make_password(new_password)
                user.save()
                otp_obj.delete()
                return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

# class ForgetPasswordAPIView(APIView):
#     permission_classes = []

#     def post(self, request):
#         try:
#             serializer = ForgetPasswordSerializer(data=request.data)
#             serializer.is_valid()

    
#             email = serializer.validated_data['email']
#             mobile_number = serializer.validated_data['mobile_number']
#             new_password = serializer.validated_data['new_password']
#             confirm_password = serializer.validated_data['confirm_password']

#             if new_password != confirm_password:
#                 raise serializers.ValidationError("Passwords do not match", code="password_mismatch")
#             # return serializer.validated_data
    
#             mobile_number = User.objects.get(mobile_number=mobile_number)

#             try:
#                 user = User.objects.get(email=email)
#             except User.DoesNotExist:
#                 return Response(
#                     {"error": "Email not found"},
#                     status=status.HTTP_404_NOT_FOUND
#                 )
    
#             user.set_password(new_password)
#             user.save()
    
#             return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class LogoutApiView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        request.user.access_token.delete()

        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
 
class EmployeeApiView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            session = Employee.objects.all()
            serializer = EmployeeSerializer(session, many = True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # def patch(self, request):
    #     serializer = EmployeeSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    def put(self, request):
        try:
            user = request.user
            if user.role.name == "HR":
                employee = Employee.objects.get(user=request.user)
                serializer = EmployeeSerializer(employee, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            if user.role.name == "EMPLOYEE":
                employee = Employee.objects.get(user=request.user)
                serializer = EmployeeDetailesCheckBoxSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save(
                        employee=employee,
                        employee_data_for_approval=request.data,
                        hr_approval="PENDING"
                    )
                    return Response({"message": "Details submitted for HR approval"}, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "Only HR and Employee can submit employee details"}, status=status.HTTP_403_FORBIDDEN)
        except Employee.DoesNotExist:
            return Response({"error": "Employee profile not found"}, status=status.HTTP_400_BAD_REQUEST)


class EmployeeEmergencyContactView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            session = EmployeeEmergencyContact.objects.all()
            serializer = EmployeeEmergencyContactSerializer(session, many = True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            user = request.user
            if user.role.name == "HR":
                employee = Employee.objects.get(user=request.user)
                serializer = EmployeeEmergencyContactSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save(employee=employee)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            if user.role.name == "EMPLOYEE":
                employee = Employee.objects.get(user=request.user)
                serializer = EmployeeDetailesCheckBoxSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save(
                        employee=employee,
                        employee_data_for_approval=request.data,
                        hr_approval="PENDING"
                    )
                    return Response({"message": "Details submitted for HR approval"}, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "Only HR and Employee can submit employee details"}, status=status.HTTP_403_FORBIDDEN)
        except Employee.DoesNotExist:
            return Response({"error": "Employee profile not found"}, status=status.HTTP_400_BAD_REQUEST)


class EmployeeAddressIdentityRequestView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        try:
            document = EmployeeAddressIdentity.objects.all()
            serializer = EmployeeAddressIdentitySerializer(document, many = True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            user = request.user
            if user.role.name == "HR":
                employee = Employee.objects.get(user=request.user)
                serializer = EmployeeAddressIdentitySerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save(employee=employee)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            if user.role.name == "EMPLOYEE":
                employee = Employee.objects.get(user=request.user)
                serializer = EmployeeDetailesCheckBoxSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save(
                        employee=employee,
                        # employee_data_for_approval=request.data,
                        hr_approval="PENDING"
                    )
                    return Response({"message": "Details submitted for HR approval"}, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "Only HR and Employee can submit employee details"}, status=status.HTTP_403_FORBIDDEN)
        except Employee.DoesNotExist:
            return Response({"error": "Employee profile not found"}, status=status.HTTP_400_BAD_REQUEST)


class EmployeeDetailApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            checkbox = EmployeeDetailesCheckBox.objects.all()
            serializer = EmployeeDetailesCheckBoxSerializer(checkbox, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except EmployeeDetailesCheckBox.DoesNotExist:
            return Response({'error': 'Employee details not found'}, status=status.HTTP_404_NOT_FOUND)
        

    def put(self, request, pk):
        user = request.user
    
        if user.role.name != "HR":
            return Response(
                {"error": "Only HR can approve"},
                status=status.HTTP_403_FORBIDDEN
            )
    
        # 2️ Get approval request
        try:
            checkbox = EmployeeDetailesCheckBox.objects.get(pk=pk)
        except EmployeeDetailesCheckBox.DoesNotExist:
            return Response(
                {"error": "Employee details not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
        # 3️ Validate approval status
        approval_status = request.data.get("hr_approval")
        if approval_status not in ["APPROVED", "REJECTED"]:
            return Response(
                {"error": "Invalid approval status"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        # 4️ Update approval status
        checkbox.hr_approval = approval_status
        checkbox.save()
    
        #  If rejected → stop here
        if approval_status == "REJECTED":
            self.send_notification(
                checkbox.employee.user,
                "Sorry, your details were REJECTED by HR. Please resubmit with correct information."
            )
            return Response(
                {"message": "Details REJECTED successfully"},
                status=status.HTTP_200_OK
            )
    
        #  APPROVED FLOW
        data = checkbox.employee_data_for_approval or {}
    
        employee_data = data.get("employee", {})
        emergency_data = data.get("emergency_contact", {})
        address_data = data.get("address_identity", {})
    
        # 5️ Atomic transaction (all or nothing)
        with transaction.atomic():
    
            #  Employee table update (only if data exists)
            if employee_data:
                Employee.objects.filter(
                    id=checkbox.employee.id
                ).update(**employee_data)
    
            #  Emergency Contact table
            if emergency_data:
                EmployeeEmergencyContact.objects.update_or_create(
                    employee=checkbox.employee,
                    defaults=emergency_data
                )
    
            #  Address & Identity table
            if address_data:
                EmployeeAddressIdentity.objects.update_or_create(
                    employee=checkbox.employee,
                    defaults=address_data
                )
    
        # 6️ Notify employee
        self.send_notification(
            checkbox.employee.user,
            "Congratulations! Your details have been APPROVED by HR."
        )
    
        return Response(
            {"message": "Details APPROVED successfully"},
            status=status.HTTP_200_OK
        )
    def send_notification(self, user, message):
        print(f"Notification to {user.username}: {message}")
    
    # def put(self, request, pk):
    #     user = request.user

    #     if user.role.name != "HR":
    #         return Response({"error": "Only HR can approve"}, status=status.HTTP_403_FORBIDDEN)
    #     try:
    #         checkbox = EmployeeDetailesCheckBox.objects.get(pk=pk)
    #     except EmployeeDetailesCheckBox.DoesNotExist:
    #         return Response({"error": "Employee details not found"}, status=status.HTTP_404_NOT_FOUND)

    #     approval_status = request.data.get("hr_approval")

    #     if approval_status not in ["APPROVED", "REJECTED"]:
    #         return Response({"error": "Invalid approval status"}, status=status.HTTP_400_BAD_REQUEST)

    #     checkbox.hr_approval = approval_status
    #     checkbox.save()

    #     if approval_status == "APPROVED":
    #         Employee.objects.update_or_create(
    #             user=checkbox.employee.user,
    #             defaults={
    #                 "full_name": checkbox.employee.full_name,
    #                 "gender": checkbox.employee.gender,
    #                 "marital_status": checkbox.employee.marital_status,
    #                 "blood_group": checkbox.employee.blood_group,
    #                 "date_of_birth": checkbox.employee.date_of_birth,
    #                 "mobile_number": checkbox.employee.mobile_number,
    #             }
    #         )

    #         EmployeeEmergencyContact.objects.update_or_create(
    #             employee=checkbox.employee,
    #             defaults={
    #                 "contact_name": checkbox.contact_name,
    #                 "designation": checkbox.designation,
    #                 "relationship": checkbox.relationship,
    #                 "phone_number": checkbox.phone_number,
    #                 "email": checkbox.email,
    #             }
    #         )

    #         EmployeeAddressIdentity.objects.update_or_create(
    #             employee=checkbox.employee,
    #             defaults={
    #                 "address_line1": checkbox.address_line1,
    #                 "address_line2": checkbox.address_line2,
    #                 "city": checkbox.city,
    #                 "state": checkbox.state,
    #                 "postal_code": checkbox.postal_code,
    #                 "country": checkbox.country,
    #                 "profile_picture": checkbox.profile_picture,
    #                 "identity_proof_type": checkbox.identity_proof_type,
    #                 "identity_proof_number": checkbox.identity_proof_number,
    #                 "identity_proof_document": checkbox.identity_proof_document,
    #                 "identity_proof_type_2": checkbox.identity_proof_type_2,
    #                 "identity_proof_number_2": checkbox.identity_proof_number_2,
    #                 "identity_proof_document_2": checkbox.identity_proof_document_2,
    #             }
    #         )
    #         self.send_notification(checkbox.employee.user,"Congratulations your address and identity details have been APPROVED by HR")
    #     else:
    #         self.send_notification(checkbox.employee.user,"Sorry your address and identity details have been REJECTED by HR. Kindly resubmit with correct details.")
    #     return Response({"message": f"Details {approval_status} successfully"},status=status.HTTP_200_OK)



class AttendanceApiView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            attendance_records = Attendance.objects.all()
            serializer = AttendanceSerializer(attendance_records, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            # print(user)
            # print(user.id)
            # if user.role.name != "EMPLOYEE":
            # FULL_DAY_HOURS = timedelta(hours=8, minutes=45)
            serializer = AttendanceSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
        
            employee = Employee.objects.filter(user=user).first()
        
            check_in_dt = serializer.validated_data.get("check_in_time")
        
            # Convert datetime → time
            check_in = check_in_dt.time() if isinstance(check_in_dt, datetime) else check_in_dt

        
            if check_in:
                check_in_td = str(timedelta(
                    hours=check_in.hour,
                    minutes=check_in.minute,
                    seconds=check_in.second,
                ))
        
            attendance = Attendance.objects.create(
                user=user,
                employee=employee,
                date=serializer.validated_data["date"],
                check_in_time=check_in_td
            )
        
            return Response(AttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)
            # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk):
        try:
            user = request.user
            FULL_DAY_HOURS = timedelta(hours=8, minutes=45)
            serializer = AttendanceSerializer(data=request.data)
            if serializer.is_valid(raise_exception= True):
                # serializer.save()
                # check_in_time = serializer.validated_data.get("check_in_time")
                check_out_time = serializer.validated_data.get("check_out_time")
                date = serializer.validated_data.get("date")

                employee = Employee.objects.filter(user=user).first()
                total_duration = timedelta(0)
                try:
                    attendance = Attendance.objects.get(employee=employee, date=date)
                except Attendance.DoesNotExist:
                    attendance = None
                check_in_time = attendance.check_in_time
                # print(check_in_time)
                status_value = "ABSENT"

                # Calculate working hours
                if check_in_time and check_out_time:
                    check_in_time_total = timedelta(
                        hours=check_in_time.hour,
                        minutes=check_in_time.minute,
                        seconds=check_in_time.second,
                    )
                    check_out_time_total = timedelta(
                        hours=check_out_time.hour,
                        minutes=check_out_time.minute,
                        seconds=check_out_time.second,
                    )

                total_duration = check_out_time_total - check_in_time_total
        
                if total_duration >= FULL_DAY_HOURS:
                    status_value = "PRESENT"
                elif total_duration > timedelta(0) and total_duration < FULL_DAY_HOURS:
                    status_value = "HALF_DAY"
                    
        
                attendance, created = Attendance.objects.update_or_create(
                    employee=employee,
                    user=user,
                    date=date,
                    # check_in_time=check_in_time,
                    defaults={
                        "check_out_time":check_out_time,
                        "total_duration":total_duration,
                        "status":status_value,
                    }
                    
                )

                response_serializer  = AttendanceSerializer(attendance)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class WorkFromHomeRequestView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         try:
#             session = WorkFromHomeRequest.objects.all()
#             serializer = WorkFromHomeRequestSerializer(session, many = True)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def post(self, request, *args, **kwargs):
#         try:
#             user = request.user
#             serializer = WorkFromHomeRequestSerializer(data=request.data)
#             serializer.is_valid(raise_exception=True)

#             employee = Employee.objects.get(user=request.user)
#             print(employee)

#             from_date = serializer.validated_data.get('from_date')
#             to_date = serializer.validated_data.get('to_date')
#             reason = serializer.validated_data.get('reason')

#             if from_date is None or to_date is None:
#                 return Response(
#                     {"error": "from_date and to_date are required"},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             if to_date < from_date:
#                 return Response(
#                     {"error": "to_date cannot be before from_date"},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             total_days = (to_date - from_date).days + 1


#             # session = WorkFromHomeRequest.objects.filter(employee=employee)
            
#             WFH_Request = WorkFromHomeRequest.objects.create(
#                 employee=employee,
#                 from_date=from_date,
#                 to_date=to_date,
#                 total_days=total_days,
#                 reason=reason,
#                 status='pending'
#             )
#             serializer = WorkFromHomeRequestSerializer(WFH_Request)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         except:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class WorkFromHomeApprovalView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         try:
#             session = WorkFromHomeApproval.objects.all()
#             serializer = WorkFromHomeApprovalSerializer(session, many = True)
#             return Response(serializer.errors, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({'errors': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#     def post(self, request):
#         serializer = WorkFromHomeApprovalSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WorkFromHomeRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return Response({"error": "Employee profile not found for this user"}, status=status.HTTP_400_BAD_REQUEST)
    
        sessions = WorkFromHomeRequest.objects.filter(employee=employee)
        serializer = WorkFromHomeRequestSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = WorkFromHomeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        employee = Employee.objects.get(user=request.user)

        from_date = serializer.validated_data["from_date"]
        to_date = serializer.validated_data["to_date"]
        reason = serializer.validated_data.get("reason")

        if to_date < from_date:
            return Response({"error": "to_date cannot be before from_date"}, status=status.HTTP_400_BAD_REQUEST)

        total_days = (to_date - from_date).days + 1

        #  Rule: Friday WFH restriction
        if from_date.weekday() == 4:
            return Response({"error": "Friday WFH is restricted"},status=status.HTTP_400_BAD_REQUEST)

        #  Rule: Bulk WFH
        if total_days >= 2:
            approval_type = "SPECIAL"
        else:
            approval_type = "NORMAL"

        wfh = WorkFromHomeRequest.objects.create(
            employee=employee,
            from_date=from_date,
            to_date=to_date,
            total_days=total_days,
            reason=reason,
            status="PENDING",
            approval_type=approval_type
        )

        return Response(WorkFromHomeRequestSerializer(wfh).data, status=status.HTTP_201_CREATED)

class WorkFromHomeApprovalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WorkFromHomeApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        role = user.role

        wfh_request = get_object_or_404(WorkFromHomeRequest,id=request.data.get("wfh_request_id"))

        # wfh_request = WorkFromHomeRequest.objects.get(employee__user=request.user)
        status_value = serializer.validated_data["status"]

        # RULE 1: SPECIAL approval → MANAGER only
        if wfh_request.approval_type == "SPECIAL" and role.name != "MANAGER":
            return Response({"error": "Bulk WFH requests require MANAGER approval"},status=status.HTTP_403_FORBIDDEN)

        # if wfh_request.approval_type == "SPECIAL" and status_value == "APPROVED":
        #     return Response()

        # RULE 2: NORMAL approval → MANAGER or HR
        if wfh_request.approval_type == "NORMAL" and role.name != "HR":
            return Response({"error": "Invalid approver role"},status=status.HTTP_403_FORBIDDEN)

        #  Save approval
        approval = serializer.save(approved_by=user, role=role, wfh_request_id=wfh_request.id )

        # FINAL STATUS UPDATE
        if status_value == "APPROVED":

            # SPECIAL → HR approval required
            if wfh_request.approval_type == "NORMAL" and role.name == "HR":
                wfh_request.status = "APPROVED"
                wfh_request.save()

            # NORMAL → manager approval is enough
            if wfh_request.approval_type == "SPECIAL" and role.name == "MANAGER":
                wfh_request.status = "APPROVED"
                wfh_request.save()

            # If manager approved but HR not
            # if wfh_request.approval_type == "SPECIAL" and wfh_request.status == "APPROVED" and role.name != "HR":
            #     return Response({"error": "Invalid approver role"},status=status.HTTP_403_FORBIDDEN)

            # NORMAL OR SPECIAL → HR must approve
            # if wfh_request.approval_type in ["NORMAL", "SPECIAL"] and role.name == "HR":
            #     wfh_request.status = "APPROVED"
            #     wfh_request.save()

                # Attendance mark
                Attendance.objects.create(
                    employee=wfh_request.employee,
                    date=wfh_request.from_date,
                    status="PRESENT"
                )

        return Response(WorkFromHomeApprovalSerializer(approval).data, status=status.HTTP_201_CREATED)


class LeaveRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Role check
        if user.role.name not in ["EMPLOYEE", "HR"]:
            return Response({"error": "Only employees can apply for leave"}, status=status.HTTP_403_FORBIDDEN)
        
        employee = Employee.objects.get(user=request.user)
        
        data = request.data

        try:

            leave_type = data.get('leave_type')
            half_day = data.get('half_day', False)
        
            from_date = datetime.strptime(data.get('from_date'), "%Y-%m-%d").date()
            to_date = datetime.strptime(data.get('to_date'), "%Y-%m-%d").date()

            if from_date > to_date:
                return Response({"error": "Invalid date range"}, status=status.HTTP_400_BAD_REQUEST)
        
            total_days = (to_date - from_date).days + 1
            # print(leave_type, total_days)

        
            if half_day:
                total_days = 0.5
        
        except Exception:
            return Response({"error": "Invalid input data"}, status=status.HTTP_400_BAD_REQUEST)
        
        # try:
        #     employee = employee
        #     leave_type = LeaveType.objects.get(id=data.get('leave_type'))
        #     half_day = data.get('half_day', False)
        #     from_date = data.get('from_date')
        #     to_date = data.get('to_date')
        #     total_days = float(from_date and to_date and (to_date - from_date).days + 1 or 0)
        # except Exception as e:
        #     return Response(
        #         {"error": "Invalid input data"},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        # print(employee, leave_type, total_days, half_day, from_date, to_date)

        # Date validation
        if from_date > to_date:
            return Response(
                {"error": "Invalid date range"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Half-day rule
        if half_day and leave_type not in ['Casual', 'Sick']:
            return Response({"error": "Half-day not allowed for this leave type"}, status=status.HTTP_400_BAD_REQUEST)

        # Overlapping leave check
        if LeaveApplication.objects.filter(
            employee=employee,
            from_date__lte=to_date,
            to_date__gte=from_date,
            status__in=['PENDING', 'APPROVED']
        ).exists():
            return Response({"error": "Leave already applied"}, status=status.HTTP_400_BAD_REQUEST)
        # print(employee)

        # Balance validation
        try:
            balance = EmployeeLeaveBalance.objects.get(employee=employee)
        except EmployeeLeaveBalance.DoesNotExist:
            return Response({"error": "Leave balance not initialized for this employee"},status=status.HTTP_400_BAD_REQUEST)

        # print(balance)

        if leave_type == 'Casual' and balance.casual_leave_balance < total_days:
            return Response({"error": "Insufficient Casual Leave"}, status=status.HTTP_400_BAD_REQUEST)

        if leave_type == 'Sick' and balance.sick_leave_balance < total_days:
            return Response({"error": "Insufficient Sick Leave"}, status=status.HTTP_400_BAD_REQUEST)

        if leave_type == 'Optional' and balance.optional_leave_balance < total_days:
            return Response({"error": "Insufficient Optional Leave"}, status=status.HTTP_400_BAD_REQUEST)

        if leave_type == 'CompOff' and balance.compoff_balance < total_days:
            return Response({"error": "Insufficient Comp-Off balance"}, status=status.HTTP_400_BAD_REQUEST)

        if balance.available_balance < total_days:
            return Response({"error": "Insufficient total balance"}, status=status.HTTP_400_BAD_REQUEST)

        # Save leave application
        serializer = LeaveApplicationSerializer(data=data)
        if serializer.is_valid():
            serializer.save(employee=employee)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ManagerLeaveApproveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, leave_id):

        leave = LeaveApplication.objects.get(id=leave_id)

        if leave.manager_approved:
            return Response({"message": "Already approved by Manager"}, status=status.HTTP_400_BAD_REQUEST)

        leave.manager_approved = True
        leave.status = 'APPROVED'
        leave.save()

        return Response({"message": "Manager approved"}, status=status.HTTP_200_OK)

class HRLeaveApproveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, leave_id):

        leave = LeaveApplication.objects.select_for_update().get(id=leave_id)

        if leave.status == 'APPROVED':
            return Response({"message": "Already approved"}, status=status.HTTP_400_BAD_REQUEST)

        # if not leave.hr_approved:
        #     return Response({"message": "HR approval required"}, status=status.HTTP_400_BAD_REQUEST)

        leave.hr_approved = True
        leave.status = 'APPROVED'
        leave.save()

        balance = EmployeeLeaveBalance.objects.select_for_update().get(employee=leave.employee)

        days = leave.total_days

        if leave.leave_type == 'Casual':
            balance.casual_leave_balance -= days
        elif leave.leave_type == 'Sick':
            balance.sick_leave_balance -= days
        # elif leave.leave_type == 'Optional':
        #     balance.optional_leave_balance -= days
        elif leave.leave_type == 'CompOff':
            balance.compoff_balance -= days
        
        balance.available_balance -= days
        balance.save()

        return Response({"message": "Leave approved & balance deducted"}, status=status.HTTP_200_OK)


class LeaveRejectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, leave_id):
        leave = LeaveApplication.objects.get(id=leave_id)

        if leave.status == 'APPROVED':
            return Response({"message": "Approved leave cannot be rejected"}, status=status.HTTP_400_BAD_REQUEST)

        leave.status = 'REJECTED'
        leave.save()

        return Response({"message": "Leave rejected"}, status=status.HTTP_200_OK)


class LeaveCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, leave_id):

        leave = LeaveApplication.objects.select_for_update().get(
            id=leave_id,
            employee=Employee.objects.get(user=request.user)
        )

        if leave.status != 'APPROVED':
            leave.status = 'CANCELLED'
            leave.save()
            return Response({"message": "Leave cancelled"}, status=status.HTTP_200_OK)

        balance = EmployeeLeaveBalance.objects.select_for_update().get(employee=request.user)

        days = leave.total_days

        if leave.leave_type == 'Casual':
            balance.casual_leave_balance += days
        elif leave.leave_type == 'Sick':
            balance.sick_leave_balance += days
        # elif leave.leave_type == 'Optional':
        #     balance.optional_leave_balance += days
        elif leave.leave_type == 'CompOff':
            balance.compoff_balance += days
        
        balance.available_balance += days
        balance.save()
        
        leave.status = 'CANCELLED'
        leave.save()

        return Response({"message": "Leave cancelled & balance reverted"}, status=status.HTTP_200_OK)
    

class CompOffCreditAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Role check
        if user.role.name not in ["HR", "MANAGER"]:
            return Response({"error": "You are not allowed to credit Comp-Off"}, status=status.HTTP_403_FORBIDDEN)

        employee_id = request.data.get("employee_id")
        days = request.data.get("days", 1)

        # Validation
        if not employee_id:
            return Response({"error": "employee_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            days = int(days)
            if days <= 0:
                raise ValueError
        except ValueError:
            return Response({"error": "days must be a positive integer"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            balance = EmployeeLeaveBalance.objects.get(employee_id=employee_id)
        except EmployeeLeaveBalance.DoesNotExist:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        # Credit comp-off
        balance.compoff_balance += days
        balance.available_balance += days
        balance.save()

        return Response({"message": f"{days} Comp-Off credited successfully"}, status=status.HTTP_200_OK)

@transaction.atomic
def approve_leave(leave):

    balance = EmployeeLeaveBalance.objects.select_for_update().get(employee=leave.employee)

    days = leave.total_days
    lt = leave.leave_type.leave_type

    if lt == 'Casual':
        balance.casual_leave_balance -= days

    elif lt == 'Sick':
        balance.sick_leave_balance -= days

    # elif lt == 'Optional':
    #     balance.optional_leave_balance -= 2 * days

    elif lt == 'CompOff':
        balance.compoff_balance -= days

    balance.available_balance -= days
    balance.save()

@transaction.atomic
def cancel_leave(leave):

    balance = EmployeeLeaveBalance.objects.select_for_update().get(employee=leave.employee)

    days = leave.total_days
    lt = leave.leave_type.leave_type

    if lt == 'Casual':
        balance.casual_leave_balance += days
    elif lt == 'Sick':
        balance.sick_leave_balance += days
    # elif lt == 'Optional':
    #     balance.optional_leave_balance += days
    elif lt == 'CompOff':
        balance.compoff_balance += days

    balance.available_balance += days
    balance.save()

@transaction.atomic
def optional_leave(leave):

    balance = EmployeeLeaveBalance.objects.select_for_update().get(employee=leave.employee)
    attendance = Attendance.objects.get(employee=leave.employee, date=leave.from_date, status="PRESENT")

    if attendance and leave.date == attendance.date and leave.leave_type == "Optional" and attendance.status == "ABSENT":
        days = leave.total_days
        balance.optional_leave_balance -= days
        balance.available_balance -= days
        balance.save()

class HolidayViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            holidays = Holiday.objects.filter(status=True)
            serializer = HolidaySerializer(holidays, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        user = request.user
        

        if user.role.name not in ["HR", "MANAGER"]:
            return Response({'error': 'You are not authorized to create holidays'}, status=status.HTTP_403_FORBIDDEN)
        serializer = HolidaySerializer(data=request.data)
        # employee = Employee.objects.filter()
        # if serializer.is_valid():
        #     print(employee)
        #     queryset_1 = EmployeeLeaveBalance.objects.all()
        #     print(queryset_1)
        #     available_balance = queryset_1.first()
        #     print(available_balance)
        #     optional_leave = serializer.validated_data.get('optional_holiday', 0)
        #     print(optional_leave)
        #     optional_leave_balance = available_balance.optional_leave_balance if available_balance else 0
        #     optional_leave_balance += optional_leave
        #     print(optional_leave_balance)
        #     approved_optional_leave = LeaveApplication.objects.filter(employee=employee, leave_type='Optional', status='APPROVED').aggregate(total=Sum('total_days'))['total'] or 0
        #     print(approved_optional_leave)
        #     optional_leave_balance -= approved_optional_leave
        #     print(optional_leave_balance)

        # return Response(serializer.data, status=status.HTTP_201_CREATED)
        # EmployeeLeaveBalance.objects.update_or_create(
        #     # employee=employee.all(),
        #     defaults={'optional_leave_balance': optional_leave_balance}
        # )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        user = request.user
        if user.role.name not in ["HR", "MANAGER"]:
            return Response({'error': 'You are not authorized to update holidays'}, status=status.HTTP_403_FORBIDDEN)
        try:
            holiday = Holiday.objects.get(pk=pk, status=True)
        except Holiday.DoesNotExist:
            return Response({'error': 'Holiday not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = HolidaySerializer(holiday, data=request.data, partial=True)
        if serializer.is_valid():
            optional_holiday = serializer.validated_data.get('optional_holiday', None)
            if optional_holiday == True:
                # Update optional leave balance for all employees
                queryset = EmployeeLeaveBalance.objects.all()
                for balance in queryset:
                    balance.optional_leave_balance += 1
                    balance.save()
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        user = request.user

        if user.role.name not in ["HR", "MANAGER"]:
            return Response({'error': 'You are not authorized to delete holidays'}, status=status.HTTP_403_FORBIDDEN)
        try:
            holiday = Holiday.objects.get(pk=pk)
        except Holiday.DoesNotExist:
            return Response({'error': 'Holiday not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # status_value = request.data.get("status")
        if holiday.status == False:
            return Response({'error': f'{holiday.name} Holiday is already deleted'}, status=status.HTTP_400_BAD_REQUEST)
        holiday.status = False
        holiday.save() 
        return Response({'message': 'Holiday deleted successfully'}, status=status.HTTP_200_OK)
    
class HrManagementAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role.name not in ["HR", "MANAGER"]:
            return Response({'error': 'you are not authorized to check the employee details'}, status=status.HTTP_403_FORBIDDEN)
        
        filterset_fields = {
            'date': ['gte', 'lte'],
            'employee': ['exact'],}
        
        total_employees = Employee.objects.filter(date__gte=..., date__lte=...)
        total_present = Attendance.objects.filter(status="Present").filter(date__gte=..., date__lte=...)
        total_leave = EmployeeLeaveBalance.objects.filter(date__gte=..., date__lte=...)
        # total_salary = Payroll.objects.aggregate(Sum('net_salary')).objects.filter(date__gte=..., date__lte=...)

        return Response({
            "total_employees": total_employees,
            "total_present": total_present,
            "total_leave": total_leave
        })


    # def post(self, request):
    #     user = request.user
    #     if user.role.name not in ["HR", "MANAGER"]:
    #         return Response({'error': 'You are not authorized to create HR management entries'}, status=status.HTTP_403_FORBIDDEN)
    #     serializer = HrManagementSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # def put(self, request, pk):
    #     user = request.user
    #     if user.role.name not in ["HR", "MANAGER"]:
    #         return Response({'error': 'You are not authorized to update HR management entries'}, status=status.HTTP_403_FORBIDDEN)
    #     try:
    #         hr_entry = HrManagement.objects.get(pk=pk)
    #     except HrManagement.DoesNotExist:
    #         return Response({'error': 'HR management entry not found'}, status=status.HTTP_404_NOT_FOUND)
    #     serializer = HrManagementSerializer(hr_entry, data=request.data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
from datetime import date
# from hrms.utils.whatsapp import send_whatsapp_message
import pywhatkit


# class whatsappAPIView(APIView):

#     def post(self, request):

#         today = date.today()

#         employees = Employee.objects.filter(
#             date_of_birth__month=today.month,
#             date_of_birth__day=today.day
#         )

#         for emp in employees:

#             # send_whatsapp_message()
#             pywhatkit.sendwhatmsg_instantly(
#                 emp.phone,
#                 f"Happy Birthday {emp.name} 🎉"
#             )

#             self.stdout.write(
#                 self.style.SUCCESS(
#                     f"Sent to {emp.name}"
#                 )
#             )


class WhatsAppAPIView(APIView):

    def post(self, request):

        today = date.today()

        employees = Employee.objects.filter(
            date_of_birth__month=today.month,
            date_of_birth__day=today.day
        )

        # print(employees)
        # print("TODAY:", today)

        # print(Employee.objects.all().values("full_name", "date_of_birth"))

        sent_employees = []
        failed_employees = []

        for emp in employees:

            try:
                phone_no=str(emp.mobile_number).strip()
                if not phone_no.startswith("+"):
                    phone = "+91" + phone_no

                # IMPORTANT:
                # phone format should be like +919876543210

                pywhatkit.sendwhatmsg_instantly(
                    phone_no=phone,
                    message=f"Happy Birthday {emp.full_name} 🎉",
                    wait_time=15,
                    tab_close=True,
                    close_time=3
                )

                sent_employees.append(emp.full_name)

            except Exception as e:

                failed_employees.append({
                    "employee": emp.full_name,
                    "error": str(e)
                })

        return Response(
            {
                "status": "completed",
                "total_birthdays": employees.count(),
                "sent": sent_employees,
                "failed": failed_employees
            },
            status=status.HTTP_200_OK
        )