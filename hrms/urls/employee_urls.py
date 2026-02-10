from django.urls import path
from rest_framework.routers import DefaultRouter
from hrms.views import *

urlpatterns = [
    path('roles/', RoleAPIView.as_view(), name='roles'),
    path('roles/<int:pk>/', RoleAPIView.as_view(), name='roles_detail'),

    path('register/', RegisterAPIView.as_view(), name='register'),

    path('forgetpassword/', ForgetPasswordView.as_view(), name='forget_p'),

    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutApiView.as_view(), name='logout'),

    path('user/', UserAPIView.as_view(), name='user'),

    path('attendance/', AttendanceApiView.as_view(), name='attendance'),
    path('attendance/<int:pk>/', AttendanceApiView.as_view(), name='attendance_detail'),

    # path('forget_password/', ForgetPasswordAPIView.as_view(), name='forget_password'),
    path('employee_master/', EmployeeApiView.as_view(), name='employee_master'),
    path('employee_master/<int:pk>/', EmployeeApiView.as_view(), name='employee_master'),
    path('employee_emergency_contact/', EmployeeEmergencyContactView.as_view(), name='employee_emergency_contact'),
    path('employee_address_identity/', EmployeeAddressIdentityRequestView.as_view(), name='employee_address_identity'),
    path('employee_address_identity/<int:pk>/', EmployeeAddressIdentityRequestView.as_view(), name='employee_address_identity_detail'),
    path('employee_details_checked_by_hr/', EmployeeDetailApiView.as_view(), name='employee_details_checkbox'),
    path('employee_details_checked_by_hr/<int:pk>/', EmployeeDetailApiView.as_view(), name='employee_details_checkbox_detail'),
    
    path('work_from_home_request/', WorkFromHomeRequestView.as_view(), name='work_from_home_request'),
    path('work_from_home_approval/', WorkFromHomeApprovalView.as_view(), name='work_from_home_approval'),

    path('leave_type/', LeaveTypeViewSet.as_view(), name='leave_type'),
    path('leave_balance/', EmployeeLeaveBalanceViewSet.as_view(), name='leave_balance'),
    path('leave_request/', LeaveRequestView.as_view(), name='leave_request'),
    path('leave_request/<int:pk>/', LeaveRequestView.as_view(), name='leave_request_detail'),
    path('admin_leave_approval/', AdminLeaveApproveAPIView.as_view(), name='admin_leave_approval'),
    path('hr_leave_approval/', HRLeaveApproveAPIView.as_view(), name= 'hr_leave_approval'),
    path('leave_approval_reject/', LeaveRejectAPIView.as_view(), name='leave_approval_reject'),
    path('leave_approval_cancel/', LeaveCancelAPIView.as_view(), name='leave_approval_cancel'),
    path('leave_approval_compoff/', CompOffCreditAPIView.as_view(), name='leave_approval_compoff'),
]