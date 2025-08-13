from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, "owner", None)
        return owner == request.user

class IsLandlord(BasePermission):
    def has_permission(self, request, view):
        p = getattr(getattr(request.user, "profile", None), "role", None)
        #print(p)
        return bool(request.user and request.user.is_authenticated and p == "LANDLORD")

class IsBookingActorOrListingOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            obj.tenant_id == request.user.id or
            obj.listing.owner_id == request.user.id
        )