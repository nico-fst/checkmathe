from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group


@receiver(post_migrate)
def create_groups(sender, **kwargs):
    if sender.name == "checkweb":
        # Check if the groups exist, and create them if not
        Group.objects.get_or_create(name="Student")
        Group.objects.get_or_create(name="Teacher")
        Group.objects.get_or_create(name="Developer")
