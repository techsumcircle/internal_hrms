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
from hrms.models import Role, MobileOTP, EmailOTP, Employee
from rest_framework.permissions import IsAuthenticated, AllowAny
from hrms.serializers.emp_serializers import *
from rest_framework_simplejwt.tokens import RefreshToken 
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import get_object_or_404
from django.contrib.postgres.search import SearchVector
from rest_framework.parsers import MultiPartParser, FormParser
# from django.contrib.auth.models import User
# from django.contrib.auth import authenticate
# from crm.models import()
# from crm.serializer import ()
# from crm.views.permission import PermissionCheckView


class RoleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            role = Role.objects.all()
            serializer = RoleSerializer(role, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request):
        try:
            serializer = RoleSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request, pk):
        try:
            role = Role.objects.get(id=pk)
            serializer = RoleSerializer(role, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Role.DoesNotExist:
            return Response({'error': 'Role does not Exists'}, status=status.HTTP_404_NOT_FOUND)
        
    def delete(self, request, pk):
        try:
            role = Role.objects.get(id=pk)
            role.delete()
            return Response({'message': 'Role deleted successfully'}, status=status.HTTP_200_OK)
        except Role.DoesNotExist:
            return Response({'error': 'Role does not Exists'}, status=status.HTTP_404_NOT_FOUND)

class RegisterAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            if user.role and user.role.name  not in ['hr', 'admin']:
                   return Response({'error': 'Kindly contact with Administrator for the registration process.'}, status=status.HTTP_400_BAD_REQUEST)

            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                # return Response({'error': serializer.data}, status=status.HTTP_400_BAD_REQUEST)
                user = serializer.save()               
                if user.role and user.role.name == 'employee': 
                    employee_num = Employee.objects.order_by('-id').first()        
                    if employee_num and employee_num.employee_id:
                        try:
                            last_transaction = int(employee_num.employee_id.replace('EMP', ''))
                            employee_id = f"EMP{last_transaction + 1:03d}"
                        except:
                            employee_id = "EMP001"
                    else:
                        employee_id = "EMP001"
                    Employee.objects.create(
                        user=user,
                        employee_id=employee_id,
                        full_name=user.get_full_name()or user.username,
                        email=user.email,
                        mobile_number=user.mobile_number,
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
            username = request.data.get('username')
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
            if request.user.role and request.user.role.name not in ['HR', 'ADMIN']:
                   return Response({'error': 'You do not have permission to view all users.'}, status=status.HTTP_403_FORBIDDEN)
            user = User.objects.all()
            serializer = UserSerializer(user, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
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
        method = request.data.get("method")       # 'email' or 'mobile'
        email_id = request.data.get("email_id")  # email or mobile
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        email = User.objects.annotate(search=SearchVector('email')).filter(search=email_id)
        
        if not method or not email_id:
            return Response({"error": "Method and email_id are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not email.exists():
            return Response({"error": "Given email ID does not exist"}, status=status.HTTP_400_BAD_REQUEST)

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
                MobileOTP.objects.filter(mobile_number=email_id).delete()
                # Save OTP
                MobileOTP.objects.create(mobile_number=email_id, otp=generated_otp, created_at=datetime.now())

                # Send SMS via Vasbay
                sms_message = f"Your OTP is {generated_otp}. Valid for 10 mins. SumCircle"
                params = {
                    "usersName": settings.VASBAY_USERNAME,
                    "key": settings.VASBAY_API_KEY,
                    "route": 2,
                    "message": sms_message,
                    "numbers": email_id,
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
                    otp_obj = MobileOTP.objects.get(mobile_number=email_id)
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
                    user = User.objects.get(mobile_number=email_id)
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
    

    def patch(self, request):
        try:
            user = request.user
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return Response({"error": "Employee profile not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = EmployeeSerializer(employee, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Employee profile updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
    
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EmployeeEmergencyContactView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            session = EmployeeEmergencyContact.objects.all()
            serializer = EmployeeEmergencyContactSerializer(session, many = True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            employee = Employee.objects.get(user=request.user)
            serializer = EmployeeEmergencyContactSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(employee=employee)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Employee.DoesNotExist:
            return Response({"error": "Employee profile not found"}, status=status.HTTP_400_BAD_REQUEST)
    
        # 2. Create using serializer ONCE
        

        # contact = EmployeeEmergencyContact.objects.get(user=request.user)
        # employee = EmployeeEmergencyContact.objects.get(employee=request.user)

        # EmployeeEmergencyContact.objects.create(
        #     employee=employee,
        #     employee_id=employee.employee_id,
        #     contact_name=request.data.get('contact_name'),
        #     designation=request.data.get('designation'),
        #     relationship=request.data.get('relationship'),
        #     phone_number=request.data.get('phone_number'),
        #     email=request.data.get('email'),
        # )
        # serializer = EmployeeEmergencyContactSerializer(employee, data=request.data)
        # if serializer.is_valid():
        #     serializer.save()
        #     return Response(serializer.data, status=status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EmployeeAddressIdentityView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    def get(self, request):
        try:
            document = EmployeeAddressIdentity.objects.all()
            serializer = EmployeeAddressIdentitySerializer(document, many = True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        parser_classes = (MultiPartParser, FormParser)
        try:

            employee = Employee.objects.get(user=request.user)
            serializer = EmployeeAddressIdentitySerializer(data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(employee=employee)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   
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
            # FULL_DAY_HOURS = timedelta(hours=8, minutes=45)
            serializer = AttendanceSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
        
            employee = Employee.objects.get(user=request.user)
        
            check_in_dt = serializer.validated_data.get("check_in_time")
        
            # ✅ Convert datetime → time
            check_in = check_in_dt.time() if isinstance(check_in_dt, datetime) else check_in_dt

#             {
#     "error": "Expected a `time`, but got a `datetime`. Refusing to coerce, as this may mean losing timezone information."
#     " Use a custom read-only field and deal with timezone issues explicitly."
# }
        
            if check_in:
                check_in_td = str(timedelta(
                    hours=check_in.hour,
                    minutes=check_in.minute,
                    seconds=check_in.second,
                ))
        
            attendance = Attendance.objects.create(
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
            FULL_DAY_HOURS = timedelta(hours=8, minutes=45)
            serializer = AttendanceSerializer(data=request.data)
            if serializer.is_valid(raise_exception= True):
                # serializer.save()
                # check_in_time = serializer.validated_data.get("check_in_time")
                check_out_time = serializer.validated_data.get("check_out_time")
                date = serializer.validated_data.get("date")
                employee = Employee.objects.get(pk=pk)
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

        # RULE 1: SPECIAL approval → ADMIN only
        if wfh_request.approval_type == "SPECIAL" and role.name != "ADMIN":
            return Response({"error": "Bulk WFH requests require ADMIN approval"},status=status.HTTP_403_FORBIDDEN)

        if wfh_request.approval_type == "SPECIAL" and status_value == "APPROVED":
            return Response()

        # RULE 2: NORMAL approval → ADMIN or HR
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
            if wfh_request.approval_type == "SPECIAL" and role.name == "ADMIN":
                wfh_request.status = "APPROVED"
                wfh_request.save()

            # If admin approved but HR not
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

        return Response(
            WorkFromHomeApprovalSerializer(approval).data, status=status.HTTP_201_CREATED)


class LeaveRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            session = LeaveApplication.objects.all()
            serializer = LeaveRequestSerializer(session, many = True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        serializer = LeaveRequestSerializer(data=request.data)
        if serializer.is_valid():
            employee = Employee.objects.get(user=request.user)

            serializer.save(employee=employee)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class LeaveTypeViewSet(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         queryset = LeaveType.objects.all()
#         serializer = LeaveTypeSerializer(queryset, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class EmployeeLeaveBalanceViewSet(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk):
#         queryset = EmployeeLeaveBalance.objects.filter(employee=self.request.user)
#         serializer = EmployeeLeaveBalanceSerializer(queryset, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class LeaveApprovalViewSet(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk=None):
#         try:
#             leave = LeaveApplication.objects.get(pk=pk)
#             if leave.manager_approved == True:
#                 leave.status = 'PENDING'
#                 leave.save()
#                 return Response({"message": "Manager approved"})
#             elif leave.hr_approved == True:
#                 leave.status = 'APPROVED'
#                 leave.save()
#                 return Response({"message": "HR approved"})
#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)