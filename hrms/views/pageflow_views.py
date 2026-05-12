from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from hrms.models import User, Book, BookIssue
from hrms.serializers.emp_serializers import *
# from .permissions import IsAuthenticated, IsNormalUser, IsOwnerOrAdmin


# Authentication Views
# class RegisterView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = RegisterSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()
#             refresh = RefreshToken.for_user(user)
#             return Response({
#                 'user': UserProfileSerializer(user).data,
#                 'tokens': {
#                     'refresh': str(refresh),
#                     'access': str(refresh.access_token),
#                 }
#             }, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class LoginView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = LoginSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.validated_data['user']
#             refresh = RefreshToken.for_user(user)
#             return Response({
#                 'user': UserProfileSerializer(user).data,
#                 'tokens': {
#                     'refresh': str(refresh),
#                     'access': str(refresh.access_token),
#                 }
#             })
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class ProfileView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         serializer = UserProfileSerializer(request.user)
#         return Response(serializer.data)

#     def put(self, request, pk):
#         serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Book Management Views
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    # def get_permissions(self):
    #     if self.action in ['list', 'retrieve']:
    #         permission_classes = [IsAuthenticated]
    #     else:
    #         permission_classes = [IsAuthenticated]
    #     return [permission() for permission in permission_classes]

    # def get_permissions(self):
    #     if self.action in ['list', 'retrieve', 'search']:
    #         return [IsAuthenticated()]
    #     return [IsAuthenticated()]

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def search(self, request):
        """Search books by title or author"""
        query = request.query_params.get('q', '')
        if query:
            books = self.queryset.filter(
                Q(title__icontains=query) |
                Q(author__icontains=query) |
                Q(unique_id__icontains=query)
            )
        else:
            books = self.queryset.all()
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)


# Issue System Views
class IssueBookView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BookIssueSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            issue = serializer.save()
            return Response(BookIssueSerializer(issue).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReturnBookView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BookReturnSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            issue = serializer.save()
            return Response({
                'message': 'Book returned successfully',
                'issue': BookIssueSerializer(issue).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyBooksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        issues = BookIssue.objects.filter(
            user=request.user
        ).select_related('book').order_by('-issue_date')

        serializer = BookIssueSerializer(issues, many=True)
        return Response(serializer.data)


# Admin Views
# class AdminUserViewSet(viewsets.ModelViewSet):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
#     permission_classes = [IsAuthenticated]


class AdminIssueViewSet(viewsets.ModelViewSet):
    queryset = BookIssue.objects.select_related('book', 'user').all()
    serializer_class = BookIssueSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active issues"""
        issues = self.queryset.filter(status='issued')
        serializer = self.get_serializer(issues, many=True)
        return Response(serializer.data)


class AdminReportsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Calculate statistics
        total_books = Book.objects.count()
        total_users = User.objects.filter(role="user").count()
        total_issues = BookIssue.objects.count()
        active_issues = BookIssue.objects.filter(status='issued').count()
        total_available_copies = sum(book.available_copies for book in Book.objects.all())

        # Most issued books
        most_issued_books = Book.objects.annotate(issue_count=Count('issues')).order_by('-issue_count')[:5]

        # Recent issues
        recent_issues = BookIssue.objects.select_related('book', 'user').order_by('-issue_date')[:10]

        data = {
            'total_books': total_books,
            'total_users': total_users,
            'total_issues': total_issues,
            'active_issues': active_issues,
            'total_available_copies': total_available_copies,
            'most_issued_books': BookSerializer(most_issued_books, many=True).data,
            'recent_issues': BookIssueSerializer(recent_issues, many=True).data,
        }

        return Response(data)

    