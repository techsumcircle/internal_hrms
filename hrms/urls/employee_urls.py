from django.urls import path
from rest_framework.routers import DefaultRouter
from hrms.views import *

urlpatterns = [
    # Authentication and User Management
    path('roles/', RoleAPIView.as_view(), name='roles'),
    path('roles/<int:pk>/', RoleAPIView.as_view(), name='roles_detail'),
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('forgetpassword/', ForgetPasswordView.as_view(), name='forget_p'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutApiView.as_view(), name='logout'),
    path('user/', UserAPIView.as_view(), name='user'),

    # Attendance Management
    path('attendance/', AttendanceApiView.as_view(), name='attendance'),
    path('attendance/<int:pk>/', AttendanceApiView.as_view(), name='attendance_detail'),

    # Employee Management
    # path('forget_password/', ForgetPasswordAPIView.as_view(), name='forget_password'),
    path('employee_master/', EmployeeApiView.as_view(), name='employee_master'),
    path('employee_master/<int:pk>/', EmployeeApiView.as_view(), name='employee_master'),
    path('employee_emergency_contact/', EmployeeEmergencyContactView.as_view(), name='employee_emergency_contact'),
    path('employee_address_identity/', EmployeeAddressIdentityRequestView.as_view(), name='employee_address_identity'),
    path('employee_address_identity/<int:pk>/', EmployeeAddressIdentityRequestView.as_view(), name='employee_address_identity_detail'),
    path('employee_details_checked_by_hr/', EmployeeDetailApiView.as_view(), name='employee_details_checkbox'),
    path('employee_details_checked_by_hr/<int:pk>/', EmployeeDetailApiView.as_view(), name='employee_details_checkbox_detail'),
    
    #Work From Home
    path('work_from_home_request/', WorkFromHomeRequestView.as_view(), name='work_from_home_request'),
    path('work_from_home_approval/', WorkFromHomeApprovalView.as_view(), name='work_from_home_approval'),

    # Leave Management
    # path('leave_type/', LeaveTypeViewSet.as_view(), name='leave_type'),
    # path('leave_balance/', EmployeeLeaveBalanceViewSet.as_view(), name='leave_balance'),
    path('leave_request/', LeaveRequestView.as_view(), name='leave_request'),
    path('leave_request/<int:pk>/', LeaveRequestView.as_view(), name='leave_request_detail'),
    path('manager_leave_approval/', ManagerLeaveApproveAPIView.as_view(), name='manager_leave_approval'),
    path('manager_leave_approval/<int:leave_id>/', ManagerLeaveApproveAPIView.as_view(), name='manager_leave_approval_detail'),
    path('hr_leave_approval/', HRLeaveApproveAPIView.as_view(), name= 'hr_leave_approval'),
    path('hr_leave_approval/<int:leave_id>/', HRLeaveApproveAPIView.as_view(), name= 'hr_leave_approval_detail'),
    path('leave_approval_reject/', LeaveRejectAPIView.as_view(), name='leave_approval_reject'),
    path('leave_approval_reject/<int:leave_id>/', LeaveRejectAPIView.as_view(), name='leave_approval_reject_detail'),
    path('leave_approval_cancel/', LeaveCancelAPIView.as_view(), name='leave_approval_cancel'),
    path('leave_approval_cancel/<int:leave_id>/', LeaveCancelAPIView.as_view(), name='leave_approval_cancel_detail'),
    path('leave_approval_compoff/', CompOffCreditAPIView.as_view(), name='leave_approval_compoff'),
    path('leave_approval_compoff/<int:leave_id>/', CompOffCreditAPIView.as_view(), name='leave_approval_compoff_detail'),

    #Holiday Management
    path('holiday/', HolidayViewSet.as_view(), name='holiday'),
    path('holiday/<int:pk>/', HolidayViewSet.as_view(), name='holiday_detail'),

    # Hr Management and Master Panel
    path('hr_management/', HrManagementAPIView.as_view(), name = 'hr_management'),

    # Salary Management
    # path('salary/', SalaryViewSet.as_view(), name='salary'),

    path('send-birthday-whatsapp/', WhatsAppAPIView.as_view(), name = 'send-birthday-whatsapp'),




    ##library_system

     # BOOKS (manual clean endpoints)
    path('books/', BookViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('books/<int:pk>/', BookViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    path('books/search/', BookViewSet.as_view({'get': 'search'})),

    # ISSUE SYSTEM
    path('issue-book/', IssueBookView.as_view()),
    path('my-books/', MyBooksView.as_view()),
    path('return-book/', ReturnBookView.as_view()),

    # ADMIN
    # path('admin/users/', AdminUserViewSet.as_view({'get': 'list', 'post': 'create'})),
    # path('admin/users/<int:pk>/', AdminUserViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    path('admin/issues/', AdminIssueViewSet.as_view({'get': 'list'})),
    path('admin/issues/active/', AdminIssueViewSet.as_view({'get': 'active'})),
    path('admin/issues/<int:pk>/', AdminIssueViewSet.as_view({'get': 'retrieve'})),

    path('admin/reports/', AdminReportsView.as_view()),

    

]