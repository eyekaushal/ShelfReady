from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrStaff(BasePermission):
    """
    Anyone can read a product. Only the user who created it, or a staff user,
    can edit or delete it.
    """

    message = "Only the product's creator or a staff member can change it."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:  # GET, HEAD, OPTIONS
            return True
        user = request.user
        return user.is_staff or obj.created_by_id == user.id
