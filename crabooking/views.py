# Create your views here.
from django.utils import timezone
from rest_framework import generics, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from .models import Listing, Booking, Review, Profile
from .filters import ListingFilter
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group, User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings
import secrets
from .serializers import (
    ListingListSerializer, ListingCreateUpdateSerializer,
    BookingCreateSerializer, BookingDetailSerializer,
    ReviewCreateSerializer, ReviewListSerializer,
    UserRegisterSerializer,
)
from .permissions import IsOwnerOrReadOnly, IsLandlord, IsBookingActorOrListingOwner

# Auth's
def set_jwt_cookies(response, user):
    """ set JWT cookies + CSRF """
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    
    csrf_token = secrets.token_urlsafe(32)
    access_token['csrf'] = csrf_token
    
    response.set_cookie(
        key='access_token',
        value=str(access_token),
        max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite='Lax',
        path='/'
    )
    
    response.set_cookie(
        key='refresh_token',
        value=str(refresh),
        max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite='Lax',
        path='/'
    )
    
    return csrf_token

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(request, username=username, password=password)
        
        if user:
            response = Response({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }, status=status.HTTP_200_OK)
            
            csrf_token = set_jwt_cookies(response, user)
            response.data['csrf_token'] = csrf_token
            
            return response
            
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

class RegistrationView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            response = Response({
                'message': 'Registration successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }, status=status.HTTP_201_CREATED)
            
            csrf_token = set_jwt_cookies(response, user)
            response.data['csrf_token'] = csrf_token
            
            return response
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                
        except TokenError:
            pass
        
        response = Response(
            {'message': 'Logout successful'},
            status=status.HTTP_200_OK
        )
        
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')
        return response


def _grant_landlord(user: User):
    prof = getattr(user, "profile", None)
    if prof and prof.role != Profile.LANDLORD:
        prof.role = Profile.LANDLORD
        prof.save(update_fields=["role"])

    group, _ = Group.objects.get_or_create(name="landlord")
    user.groups.add(group)


class PromoteLandlordAdminView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"detail":"user_id is required"}, status=400)
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail":"user not found"}, status=404)
        _grant_landlord(user)
        return Response({"status":"ok","user_id":user.id})


class PromoteLandlordSelfView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = request.data.get("invite_code")
        if not code or code != settings.LANDLORD_INVITE_CODE:
            return Response({"detail":"invalid code"}, status=403)
        _grant_landlord(request.user)
        return Response({"status":"ok"}, status=status.HTTP_200_OK)


# Listings
class ListingListCreateView(generics.ListCreateAPIView):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = ListingFilter
    search_fields = ["title","description"]
    ordering_fields = ["price_per_day","created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = Listing.objects.all().select_related("owner")
        if self.request.query_params.get("is_active") is None:
            qs = qs.filter(is_active=True)
        return qs

    def get_permissions(self):
        if self.request.method in ["POST"]:
            return [permissions.IsAuthenticated(), IsLandlord()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        return ListingCreateUpdateSerializer if self.request.method == "POST" else ListingListSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class ListingDetailUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Listing.objects.all()
    permission_classes = [IsOwnerOrReadOnly]
    def get_serializer_class(self):
        return ListingCreateUpdateSerializer if self.request.method in ["PUT","PATCH"] else ListingListSerializer

# Reviews
class ListingReviewsListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Review.objects.none()
        pk = self.kwargs.get("pk")
        return Review.objects.filter(listing_id=pk).select_related("author")
    def get_permissions(self):
        return [permissions.IsAuthenticated()] if self.request.method == "POST" else [permissions.AllowAny()]
    def get_serializer_class(self):
        return ReviewCreateSerializer if self.request.method == "POST" else ReviewListSerializer
    def perform_create(self, serializer):
        serializer.save()

# Bookings
class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Booking.objects.all()

class BookingMineListView(generics.ListAPIView):
    serializer_class = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Booking.objects.filter(tenant=self.request.user).select_related("listing")

class BookingDetailView(generics.RetrieveAPIView):
    serializer_class = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsBookingActorOrListingOwner]
    queryset = Booking.objects.select_related("listing")

class BookingApproveView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        b = Booking.objects.select_related("listing").get(pk=pk)
        if b.listing.owner_id != request.user.id:
            return Response({"detail":"Not allowed"}, status=403)
        if Booking.overlaps_approved(b.listing_id, b.date_from, b.date_to):
            return Response({"detail":"Overlaps with existing approved booking"}, status=400)
        b.status = Booking.APPROVED
        b.save(update_fields=["status"])
        return Response({"status": b.status})

class BookingRejectView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        b = Booking.objects.select_related("listing").get(pk=pk)
        if b.listing.owner_id != request.user.id:
            return Response({"detail":"Not allowed"}, status=403)
        b.status = Booking.REJECTED
        b.save(update_fields=["status"])
        return Response({"status": b.status})

class BookingCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        b = Booking.objects.get(pk=pk)
        if b.tenant_id != request.user.id:
            return Response({"detail":"Not allowed"}, status=403)
        today = timezone.now().date()
        if b.status == Booking.REQUESTED or (b.status == Booking.APPROVED and today < b.date_from):
            b.status = Booking.CANCELLED
            b.save(update_fields=["status"])
            return Response({"status": b.status})
        return Response({"detail":"Cannot cancel now"}, status=400)
