from django.urls import path
from rest_framework.routers import DefaultRouter
from hrms.views import *

urlpatterns = [
    path('roles/', RoleAPIView.as_view(), name='roles'),
    path('user/', UserAPIView.as_view(), name='user'),
    path('forgetpassword/', ForgetPasswordView.as_view(), name='forget_p'),
    path('employee/registerandlogin_sendotp/', SendMobileOTPRegistrationLogin.as_view(), name='employee_registration_login_api'),
    # path('employee/verifyotp_registerandlogin/', employeeVerifyOTPAndRegisterLoginView.as_view(), name='verifyotp_registerandlogin_api'),
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('forget_password/', ForgetPasswordAPIView.as_view(), name='forget_password'),
    path('logout/', LogoutApiView.as_view(), name='logout'),
    path('employee_master/', EmployeeApiView.as_view(), name='employee_master'),
    path('employee_master/<int:pk>/', EmployeeApiView.as_view(), name='employee_master'),
    path('employee_emergency_contact/', EmployeeEmergencyContactView.as_view(), name='employee_emergency_contact'),
    path('employee_address_identity/', EmployeeAddressIdentityView.as_view(), name='employee_address_identity'),
    path('attendance/', AttendanceApiView.as_view(), name='attendance'),
    path('attendance/<int:pk>/', AttendanceApiView.as_view(), name='attendance'),

    # path('holiday/', HolidayView.as_view(), name='holiday'),
    # # path('department/', DepartmentView.as_view(), name='department'),
    # path('salary/', SalaryView.as_view(), name='salary'),
    # path('leave_request/', LeaveRequestView.as_view(), name='leave_request'),
    # path('work_from_home_request/', WorkFromHomeRequestView.as_view(), name='work_from_home_request'),
    # path('work_from_home_approval/', WorkFromHomeApprovalView.as_view(), name='work_from_home_request')
]
