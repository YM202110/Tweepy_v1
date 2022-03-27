from django.urls import path
from . import views

urlpatterns = [
    path("", views.Index.as_view(), name="index"),
    path("register/", views.register_keyword, name='register'),
    path("gettweet/", views.get_tweets_view, name='gettweet'),
    path("searchcriteria/", views.SearchCriteria.as_view(), name='searchcriteria'),
    path("analysis/", views.TweetAnalysis.as_view(), name="analysis")
#    path("analysis/", views.TwitterAnalysis3.as_view(), name="analysis"),
]