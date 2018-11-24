from django.db import connection

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Check for destructive migrations.'

    def handle(self, *args, **options):
        pass

    def _get_all_migration_changes(self):
        """
        Get all migrations from migrations package from all apps.
        """
        pass

    def _get_all_migrations_from_db(self):
        """
        Get all applied migrations from the database.
        """
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM django_migrations;")
            rows = cursor.fetchall()

        self._group_migration_by_apps(rows)

    @staticmethod
    def _group_migration_by_apps(rows):
        """
        Group migrations by apps. The return value is a dictionary.

        {
            "app": [
                ...migrations
            ]
        }
        """
        print(rows)
