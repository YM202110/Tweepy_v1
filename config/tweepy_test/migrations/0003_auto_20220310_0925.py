# Generated by Django 3.2.8 on 2022-03-10 00:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tweepy_test', '0002_tweetkeyword'),
    ]

    operations = [
        migrations.AddField(
            model_name='tweets',
            name='keyword',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='tweepy_test.tweetkeyword', verbose_name='検索キーワード'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='tweets',
            name='tweet_id',
            field=models.CharField(max_length=255, verbose_name='ツイートID'),
        ),
        migrations.AddConstraint(
            model_name='tweets',
            constraint=models.UniqueConstraint(fields=('keyword', 'tweet_id'), name='tweet_unique'),
        ),
    ]
