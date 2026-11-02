from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0075_remove_radiologia_pacs"),
    ]

    operations = [
        migrations.AddField(
            model_name="loja",
            name="agenda_visual",
            field=models.CharField(
                blank=True,
                default="pulse",
                help_text="Tema FullCalendar 7 da visão Mês: pulse, breezy, monarch, forma ou classic.",
                max_length=20,
            ),
        ),
    ]
