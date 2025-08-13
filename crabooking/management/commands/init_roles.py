from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = "Create base groups: tenant, landlord"
    def handle(self, *args, **kwargs):
        for name in ["tenant","landlord"]:
            Group.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS("Groups ensured: tenant, landlord"))
