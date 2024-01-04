from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from checkweb.models import User
from rest_framework.authtoken.models import Token


@receiver(post_migrate)
def create_groups(sender, **kwargs):
    """Create default Groups"""
    if sender.name == "checkweb":
        # Check if the groups exist, and create them if not
        Group.objects.get_or_create(name="Student")
        Group.objects.get_or_create(name="Teacher")
        Group.objects.get_or_create(name="Developer")

@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """Creates token for newly created User"""
    if created:
        Token.objects.create(user=instance)