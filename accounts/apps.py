from django.apps import AppConfig
from django.db.models.signals import post_migrate

class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        from .roles import create_roles
        post_migrate.connect(lambda **kwargs: create_roles(), sender=self)
        import accounts.signals