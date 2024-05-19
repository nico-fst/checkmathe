from django.db.models.signals import post_migrate, pre_delete
from django.contrib.auth.signals import user_logged_out, user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from checkweb.models import User, Tutoring, Subject
from rest_framework.authtoken.models import Token
from datetime import date, datetime, timedelta
from django.utils import timezone


def create_demo_user():
    """Creates demo User with Tutorings today and in the past"""
    if not User.objects.filter(username="demo_user").exists():
        demo_user = User.objects.create_user(
            "demo_user",
            "demo.user@mail.de",
            "123",
            first_name="Demo",
            last_name="User",
            preis_pro_45=20,
        )
        demo_user.save()


@receiver(user_logged_in)
def creae_demo_user_content(sender, request, user, **kwargs):
    """(Only) when demo users logs in, creae demo Tutorings"""
    if user and user.username == "demo_user":
        demo_user = User.objects.create_user(
            "demo_user",
            "demo.user@mail.de",
            "123",
            first_name="Demo",
            last_name="User",
            preis_pro_45=20,
        )
        demo_user.save()

        if not User.objects.filter(username="xavier.x").exists():
            demo_teacher = User.objects.create_user(
                "xavier.x",
                "xavier.x@mail.de",
                "123",
                first_name="Xavier",
                last_name="X",
            )
            demo_teacher.groups.set([Group.objects.get(name="Teacher")])
            demo_teacher.save()
        else:
            demo_teacher = User.objects.get(username="xavier.x")
            demo_teacher.groups.set([Group.objects.get(name="Teacher")])

        math = Subject.objects.get_or_create(title="Math")[0]
        chemistry = Subject.objects.get_or_create(title="Chemistry")[0]

        tut_today = Tutoring.objects.create(
            date=timezone.now().date(),
            duration=45,
            subject=math,
            student=demo_user,
            teacher=demo_teacher,
            content="Ich habe den Satz des Pythagoras aus dem Unterricht noch einmal anschaulich erklärt und wir haben zusammen an Beispielaufgaben geübt. Ihr fällt es noch schwer, die Aufgaben im Kontext in Textaufgaben zu lösen, deshalb habe ich ihr für nächstes Mal ein paar Aufgaben mit Tipps mitgegeben, an denen sie sich alleine versucht. Wir werden sie beim nächsten Mal besprechen und schauen, wobei ich ihr aufbauend helfen kann.",
        )
        tut_today.save()
        tut_last = Tutoring.objects.create(
            date=timezone.now().date() - timedelta(days=3),
            duration=45,
            subject=chemistry,
            student=demo_user,
            teacher=demo_teacher,
            content="Wir haben ihre Aufgaben zu Redoxgleichungen besprochen: Das Thema hat sie gut verstanden, es hapert eher an Grundbegriffen aus dem letzten Schuljahr, als der Lehrer so lange krank war. Nächstes Mal wiederholen wir im ersten Teil deshalb vor allem Oxidationszahlen, Strukturformeln.",
        )
        tut_last.save()
        tut_last_last = Tutoring.objects.create(
            date=timezone.now().date() - timedelta(days=7),
            duration=45,
            subject=math,
            student=demo_user,
            teacher=demo_teacher,
            content="Durch die aufgegebenen Rechenaufgaben kann sie den Satz des Pythagoras nun in verschiedenen Sachkontexten zielsicher anwenden. Wir haben den Satz heute mit Geometrie verbunden (vor allem Pythagoras im Dreidimensionalen) und ich habe ihr wieder Aufgaben mit Tipps mitgegeben. Damit kann sie versuchen, ihr räumliches Verständnis noch besser mit Mathematik zu verbinden.",
        )
        tut_last_last.save()

        # TODO add PDFs to Tutorings


@receiver(post_migrate)
def create_groups(sender, **kwargs):
    """Create default Groups if not existing"""
    if sender.name == "checkweb":
        # Check if the groups exist, and create them if not
        Group.objects.get_or_create(name="Student")
        Group.objects.get_or_create(name="Teacher")
        Group.objects.get_or_create(name="Developer")

@receiver(post_migrate)
def create_subjects(sender, **kwargs):
    """Create default Subjects if not existing"""
    if sender.name == "checkweb":
        for sbj in {"Art", "Biology", "Chemistry", "English", "French", "German", "History", "Latin", "Math", "Physics", "Spanish", "Other"}:
            Subject.objects.get_or_create(title=sbj)
        

@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """Creates token for newly created User"""
    if created:
        Token.objects.create(user=instance)


@receiver(post_migrate)
def trigger_demo_user_creation(sender, **kwargs):
    """Trigger creating demo user"""
    if sender.name == "checkweb":
        create_demo_user()


@receiver(user_logged_out)
def reset_demo_user(sender, request, user, **kwargs):
    """Deletes and recreates the demo user and all its Tutorings on its logout."""
    if user and user.username == "demo_user":
        user.delete()
        create_demo_user()

@receiver(pre_delete, sender=Tutoring)
def delete_tutoring_pdf(sender, instance, **kwargs):
    if instance.pdf:
        instance.pdf.delete(save=False)
