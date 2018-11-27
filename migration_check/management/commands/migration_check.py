import sys
import pkgutil
from importlib import import_module, reload

from django.apps import apps
from django.db import connection
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.migrations.operations import fields, models

from migration_check.rules import DESTRUCTIVE_OPERATIONS, NON_DESTRUCTIVE_OPERATIONS

MIGRATIONS_MODULE_NAME = "migrations"


class Command(BaseCommand):
    help = 'Check for destructive migrations.'

    def handle(self, *args, **options):
        self._get_migrations()

    def _get_migrations(self):
        self.load_disk()

        changes = self._get_all_migration_changes()

        for change in changes:
            changed_migration = changes[change]
            operations = changed_migration.operations

            for operation in operations:
                if hasattr(operation, "field"):
                    field_null_option = operation.field.null
                else:
                    field_null_option = None
                print(self._validate_rules(operation, field_null_option))

    def _validate_rules(self, operation, field_null_option):
        destructive_rules = DESTRUCTIVE_OPERATIONS
        is_destructive = False

        destructive_fields = {
            "fields": []
        }

        for rule in destructive_rules:
            if issubclass(operation.__class__, rule):
                # Check field options
                rule_value = destructive_rules[rule]
                if rule_value["field_options"]:
                    if rule_value["field_options"]["null"] == field_null_option:
                        is_destructive = True
                        destructive_fields["fields"].append(self._get_model_field(operation))
                else:
                    is_destructive = True
                    destructive_fields["fields"].append(self._get_model_field(operation))

        return is_destructive, destructive_fields

    @staticmethod
    def _get_model_field(operation):
        if operation.__class__ == models.DeleteModel:
            return operation.name
        model_field = "{}.{}".format(operation.model_name, operation.name)
        return model_field

    def _get_all_migration_changes(self):
        """
        Get all migrations from migrations package from all apps.
        """
        disk_migrations = self.disk_migrations

        db_migrations = self._get_all_migrations_from_db()
        unapplied_migrations = {}

        db_migrations_set = self._create_db_migration_set(db_migrations)

        for disk_migration in disk_migrations:
            if disk_migration not in db_migrations_set:
                unapplied_migrations[disk_migration] = disk_migrations[disk_migration]

        return unapplied_migrations

    @staticmethod
    def _create_db_migration_set(db_migrations):
        db_migrations_set = set()

        for db_migration in db_migrations:
            key = (db_migration['app'], db_migration['name'])
            db_migrations_set.add(key)

        return db_migrations_set

    @staticmethod
    def dictfetchall(cursor):
        """Return all rows from a cursor as a dict"""
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    def _get_all_migrations_from_db(self):
        """
        Get all applied migrations from the database.
        """
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM django_migrations;")
            rows = self.dictfetchall(cursor)

        return rows

    @classmethod
    def migrations_module(cls, app_label):
        """
        Return the path to the migrations module for the specified app_label
        and a boolean indicating if the module is specified in
        settings.MIGRATION_MODULE.

        Code taken from Django.
        """
        if app_label in settings.MIGRATION_MODULES:
            return settings.MIGRATION_MODULES[app_label], True
        else:
            app_package_name = apps.get_app_config(app_label).name
            return '%s.%s' % (app_package_name, MIGRATIONS_MODULE_NAME), False

    def load_disk(self):
        """
        Load the migrations from all INSTALLED_APPS from disk.

        Code taken from Django.
        """
        self.disk_migrations = {}
        self.unmigrated_apps = set()
        self.migrated_apps = set()

        for app_config in apps.get_app_configs():
            # Get the migrations module directory
            module_name, explicit = self.migrations_module(app_config.label)
            if module_name is None:
                self.unmigrated_apps.add(app_config.label)
                continue
            was_loaded = module_name in sys.modules
            try:
                module = import_module(module_name)
            except ImportError as e:
                # I hate doing this, but I don't want to squash other import errors.
                # Might be better to try a directory check directly.
                if ((explicit and self.ignore_no_migrations) or (
                        not explicit and "No module named" in str(e) and MIGRATIONS_MODULE_NAME in str(e))):
                    self.unmigrated_apps.add(app_config.label)
                    continue
                raise
            else:
                # Empty directories are namespaces.
                # getattr() needed on PY36 and older (replace w/attribute access).
                if getattr(module, '__file__', None) is None:
                    self.unmigrated_apps.add(app_config.label)
                    continue
                # Module is not a package (e.g. migrations.py).
                if not hasattr(module, '__path__'):
                    self.unmigrated_apps.add(app_config.label)
                    continue
                # Force a reload if it's already loaded (tests need this)
                if was_loaded:
                    reload(module)
            self.migrated_apps.add(app_config.label)
            migration_names = {
                name for _, name, is_pkg in pkgutil.iter_modules(module.__path__)
                if not is_pkg and name[0] not in '_~'
            }
            # Load migrations
            for migration_name in migration_names:
                migration_path = '%s.%s' % (module_name, migration_name)
                try:
                    migration_module = import_module(migration_path)
                except ImportError as e:
                    if 'bad magic number' in str(e):
                        raise ImportError(
                            "Couldn't import %r as it appears to be a stale "
                            ".pyc file." % migration_path
                        ) from e
                    else:
                        raise
                if not hasattr(migration_module, "Migration"):
                    raise BadMigrationError(
                        "Migration %s in app %s has no Migration class" % (migration_name, app_config.label)
                    )
                self.disk_migrations[app_config.label, migration_name] = migration_module.Migration(
                    migration_name,
                    app_config.label,
                )