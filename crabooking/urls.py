from django.urls import path
from .views import (
    ListingListCreateView, ListingDetailUpdateDeleteView,
    ListingReviewsListCreateView,
    BookingCreateView, BookingMineListView, BookingDetailView,
    BookingApproveView, BookingRejectView, BookingCancelView,
    LoginView,
    RegistrationView,
    LogoutView,
    PromoteLandlordAdminView,
    PromoteLandlordSelfView,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Shema for whole site",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="webmaster@wiru.site"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('swagger.<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path("listings/", ListingListCreateView.as_view(), name='bookings'),
    path("listings/<int:pk>/", ListingDetailUpdateDeleteView.as_view(), name='booking-detail'),
    path("listings/<int:pk>/reviews/", ListingReviewsListCreateView.as_view(), name='bookings'),

    path("bookings/", BookingCreateView.as_view(), name='bookings'),
    path("bookings/mine/", BookingMineListView.as_view(), name='users-bookings'),
    path("bookings/<int:pk>/", BookingDetailView.as_view(), name='booking-detail'),
    path("bookings/<int:pk>/approve/", BookingApproveView.as_view(), name='booking-approve'),
    path("bookings/<int:pk>/reject/", BookingRejectView.as_view(), name='booking-reject'),
    path("bookings/<int:pk>/cancel/", BookingCancelView.as_view(), name='booking-cancel'),

    path('login/', LoginView.as_view(), name='login'),
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("promote/", PromoteLandlordAdminView.as_view()),
    path("promoteself/", PromoteLandlordSelfView.as_view()),
]
