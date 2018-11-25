from django.db.migrations.operations import fields, models


DESTRUCTIVE_OPERATIONS = {
    fields.RemoveField: {
        "field_options": {}
    },
    fields.RenameField: {
        "field_options": {}
    },
    models.DeleteModel: {
        "field_options": {}
    },
    models.AlterModelTable: {
        "field_options": {}
    },
    fields.AddField: {
        "field_options": {
            "null": False
        }
    }
}

NON_DESTRUCTIVE_OPERATIONS = {
    fields.AddField: {
        "field_options": {
            "null": True
        }
    },
    models.CreateModel: {
        "field_options": {}
    },
}
