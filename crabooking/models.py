from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone

# Create your models here.

User = settings.AUTH_USER_MODEL

class Profile(models.Model):
    TENANT = "TENANT"
    LANDLORD = "LANDLORD"
    ROLE_CHOICES = [(TENANT, "Tenant"), (LANDLORD, "Landlord")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=TENANT)
    phone = models.CharField(max_length=32, blank=True, null=True)

    def __str__(self):
        return f"{self.user} ({self.role})"


class Listing(models.Model):
    APARTMENT = "APARTMENT"
    HOUSE = "HOUSE"
    STUDIO = "STUDIO"
    TYPE_CHOICES = [(APARTMENT, "Apartment"), (HOUSE, "House"), (STUDIO, "Studio")]

    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name="listings")
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    city = models.CharField(max_length=80)
    district = models.CharField(max_length=80, blank=True)
    price_per_day = models.DecimalField(max_digits=12, decimal_places=2)
    rooms = models.PositiveSmallIntegerField()
    property_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default=APARTMENT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(Lower("city"), name="listing_city_lower_idx"),
            models.Index(fields=["price_per_day"], name="listing_price_idx"),
            models.Index(fields=["rooms"], name="listing_rooms_idx"),
            models.Index(fields=["created_at"], name="listing_created_idx"),
        ]

    def __str__(self):
        return f"{self.title} {self.city} {self.price_per_day}€"


class Booking(models.Model):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    STATUS_CHOICES = [(REQUESTED,"Requested"),(APPROVED,"Approved"),(REJECTED,"Rejected"),(CANCELLED,"Cancelled")]

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bookings")
    tenant = models.ForeignKey(User, on_delete=models.PROTECT, related_name="bookings")
    date_from = models.DateField()
    date_to = models.DateField()
    status = models.CharField(max_length=16 , choices=STATUS_CHOICES, default=REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["listing","status","date_from","date_to"], name="booking_main_idx"),
        ]

    def __str__(self):
        return f"{self.listing_id} {self.tenant_id} {self.date_from}->{self.date_to} [{self.status}]"

    @staticmethod
    def overlaps_approved(listing_id, start, end):
        return Booking.objects.filter(
            listing_id=listing_id,
            status=Booking.APPROVED,
        ).filter(
            Q(date_from__lte=end) & Q(date_to__gte=start)
        ).exists()


class Review(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="reviews")
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name="reviews")
    rating = models.PositiveSmallIntegerField()
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["listing", "author"], name="review_once_per_user"),
        ]

    def __str__(self):
        return f"*{self.rating} on {self.listing_id} by {self.author_id}"
