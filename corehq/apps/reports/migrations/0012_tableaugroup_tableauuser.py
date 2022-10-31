# Generated by Django 3.2.15 on 2022-10-31 20:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0011_tableauconnectedapp'),
    ]

    operations = [
        migrations.CreateModel(
            name='TableauGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('group_id', models.CharField(max_length=32)),
                ('server', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reports.tableauserver')),
            ],
        ),
        migrations.CreateModel(
            name='TableauUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=64)),
                ('role', models.CharField(choices=[('Explorer - Can Publish', 'ExplorerCanPublish'), ('Server Administrator', 'ServerAdministrator'), ('Site Administrator - Explorer', 'SiteAdministratorExplorer'), ('Site Administrator - Creator', 'SiteAdministratorCreator'), ('Unlicensed', 'Unlicensed'), ('Read Only', 'ReadOnly'), ('Viewer', 'Viewer')], max_length=32)),
                ('tableau_user_id', models.CharField(max_length=64)),
                ('last_synced', models.DateTimeField(auto_now=True)),
                ('groups', models.ManyToManyField(to='reports.TableauGroup')),
                ('server', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reports.tableauserver')),
            ],
        ),
    ]
