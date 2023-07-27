from django.db import migrations

payment_point_rights = [201001, 201002, 201003, 201004]
imis_administrator_system = 64


def add_rights(apps, schema_editor):
    role = apps.get_model('core', 'role').objects.get(is_system=imis_administrator_system)
    for right_id in payment_point_rights:
        if not apps.get_model('core', 'roleright').objects.filter(validity_to__isnull=True, role=role,
                                                                  right_id=right_id).exists():
            _add_right_for_role(apps, role, right_id)


def _add_right_for_role(apps, role, right_id):
    apps.get_model('core', 'roleright').objects.create(role=role, right_id=right_id, audit_user_id=1)


def remove_rights(apps, schema_editor):
    apps.get_model('core', 'roleright').objects.filter(
        role__is_system=imis_administrator_system,
        right_id__in=payment_point_rights,
        validity_to__isnull=True
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('payroll', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_rights, remove_rights),
    ]
