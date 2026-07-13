from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    def ready(self):
        """Connect cache-clear signals for CMS models.
        Called after Django app registry is fully loaded."""
        from . import signals
        signals.connect_signals()
