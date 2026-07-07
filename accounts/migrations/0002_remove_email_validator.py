from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Remove o validator validate_email_institucional do campo email ao nível da BD.
    A validação passa a ser feita no User.clean(), que só a aplica a não-staff,
    permitindo criar superutilizadores com qualquer email via createsuperuser.
    """

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(
                max_length=254,
                unique=True,
                verbose_name='Email institucional',
            ),
        ),
    ]
