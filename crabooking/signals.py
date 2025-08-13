from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from crabooking.mails import send_landlord_invite_email
from .models import Profile



User = get_user_model()

@receiver(post_save, sender=User)
def create_profile_and_default_role(sender, instance, created, **kwargs):
    if not created:
        return
    Profile.objects.create(user=instance, role=Profile.TENANT)
    try:
        tenant_group, _ = Group.objects.get_or_create(name="tenant")
        instance.groups.add(tenant_group)
    except Exception:
        pass

    send_landlord_invite_email(instance)