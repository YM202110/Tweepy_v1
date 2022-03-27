import tweepy
from django.conf import settings

def get_tweets(searchkey, location, item_num):
    api_key       = settings.API_KEY
    api_secret    = settings.API_SECRET
    access_key    = settings.ACCESS_KEY
    access_secret = settings.ACCESS_SECRET

    auth = tweepy.OAuth1UserHandler(api_key, api_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)
    
    search_criteria = "{0} {1}".format(searchkey, location)

    # API連携してツイート情報を収集（位置情報はqueryオペレーターに入れる）
    # fromDate入れないと過去30日遡ってしまう。。
    tweets = tweepy.Cursor(api.search_30_day, label='test1', query=search_criteria, fromDate='202203080000').pages(item_num)


    tweets = list(tweets)
    tweet_data = []
    for i in range(len(tweets)):
        for tweet in tweets[i]:
            if not 'RT @' in tweet.text[:4]:
                tweet_data.append([searchkey, tweet.id, tweet.user.id, tweet.user.name, tweet.text, tweet.favorite_count, tweet.retweet_count, tweet.created_at])

    return tweet_data
