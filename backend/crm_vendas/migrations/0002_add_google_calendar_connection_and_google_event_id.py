# Generated manually for Google Calendar sync (google_event_id only; GoogleCalendarConnection is in superadmin)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='atividade',
            name='google_event_id',
            field=models.CharField(blank=True, help_text='ID do evento no Google Calendar (sincronização)', max_length=255, null=True),
        ),
    ]
