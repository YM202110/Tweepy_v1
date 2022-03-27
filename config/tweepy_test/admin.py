from django.contrib import admin
from .models import Tweets, TweetKeyword
# Register your models here.
admin.site.register(Tweets)
admin.site.register(TweetKeyword)