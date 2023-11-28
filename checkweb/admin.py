from django.contrib import admin
from .models import Role, User, Subject, Tutoring

# Register your models here.
admin.site.register(Role)
admin.site.register(User)
admin.site.register(Subject)
admin.site.register(Tutoring)
