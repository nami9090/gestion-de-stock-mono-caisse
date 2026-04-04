from django.contrib.auth.models import Group


def create_roles():
    roles = [
        "Admin",
        "Caisse"
    ]
    for role_name in roles:
        Group.objects.get_or_create(name=role_name)