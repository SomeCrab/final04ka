import django_filters as df
from .models import Listing

class ListingFilter(df.FilterSet):
    price_min = df.NumberFilter(field_name="price_per_day", lookup_expr="gte")
    price_max = df.NumberFilter(field_name="price_per_day", lookup_expr="lte")
    rooms_min = df.NumberFilter(field_name="rooms", lookup_expr="gte")
    rooms_max = df.NumberFilter(field_name="rooms", lookup_expr="lte")
    city = df.CharFilter(field_name="city", lookup_expr="iexact")
    property_type = df.CharFilter(field_name="property_type", lookup_expr="iexact")
    is_active = df.BooleanFilter(field_name="is_active")

    class Meta:
        model = Listing
        fields = ["price_min","price_max","rooms_min","rooms_max","city","property_type","is_active"]