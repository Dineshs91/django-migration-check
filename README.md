# django-migration-check
This package lets you know if migrations can be run safely.

## Support

This package works with Django>2.0 only.

## Usage

Run this command after migrations are generated and before they are applied.

Ideally it would be like this

```
python manage.py makemigrations
python manage.py migration_check

python manage.py migrate
```
