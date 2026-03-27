# Generated manually - remove HeroSection.imagem (banner usa só HeroImagem / carrossel)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0039_heroimagem'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='herosection',
            name='imagem',
        ),
    ]
