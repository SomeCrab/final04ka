from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import Listing, Booking, Review
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password as default_validate_password


class TrackFieldUpdatesMixin:
    def update(self, instance, validated_data):
        m2m_fields = {}
        update_fields = []
        
        for field_name, value in validated_data.items():
            field = self.Meta.model._meta.get_field(field_name)
            if field.many_to_many:
                m2m_fields[field_name] = value
            else:
                # Only add to update_fields if the value actually changed
                if getattr(instance, field_name) != value:
                    setattr(instance, field_name, value)
                    update_fields.append(field_name)
        
        # Add auto_now fields that will be updated
        if m2m_fields or update_fields:
            auto_now_fields = [
                field.name for field in self.Meta.model._meta.get_fields()
                if getattr(field, 'auto_now', False)
            ]
            update_fields.extend(auto_now_fields)
        #print(update_fields)
        # Save with update_fields if there are changes
        if update_fields:
            instance.save(update_fields=update_fields)
        
        # Set M2M fields after save
        for field_name, value in m2m_fields.items():
            getattr(instance, field_name).set(value)
        
        return instance


class ListingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ["id","owner","title","description","city","district",
                  "price_per_day","rooms","property_type","is_active",
                  "created_at","updated_at"]

class ListingCreateUpdateSerializer(TrackFieldUpdatesMixin, serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ['id',"title","description","city","district","price_per_day",
                  "rooms","property_type","is_active",'created_at','updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["listing","date_from","date_to"]
        read_only_fields = ['id', 'tenant', 'status', 'created_at']
    def validate(self, attrs):
        user = self.context["request"].user
        listing = attrs["listing"]
        if listing.owner_id == user.id:
            raise serializers.ValidationError("Owner cannot book own listing.")
        if attrs["date_from"] > attrs["date_to"]:
            raise serializers.ValidationError("date_from must be <= date_to.")
        return attrs
    def create(self, validated):
        validated["tenant"] = self.context["request"].user
        return super().create(validated)

class BookingDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["id","listing","tenant","date_from","date_to","status","created_at"]

class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["listing","rating","text"]
    def validate_rating(self, v):
        if not 1 <= v <= 5:
            raise serializers.ValidationError("Rating must be 1..5.")
        return v
    def validate(self, attrs):
        user = self.context["request"].user
        listing = attrs["listing"]
        if Review.objects.filter(listing=listing, author=user).exists():
            raise serializers.ValidationError("You have already left a review for this listing.")
        today = timezone.now().date()
        had_stay = Booking.objects.filter(
            listing=listing, tenant=user, status=Booking.APPROVED, date_to__lte=today
        ).exists()
        if not had_stay:
            raise serializers.ValidationError("You can review only after a completed approved booking!")
        return attrs
    def create(self, validated):
        validated["author"] = self.context["request"].user
        return super().create(validated)

class ReviewListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id","author","rating","text","created_at"]


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'password', 'email']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', '')
        )
        return user
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(f"Username {value} is taken.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("You cant register multiple accounts on same email.")
        return value

    def validate_password(self, value):
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain at least one upper character.")
        
        default_validate_password(value)

        return value
