from django.db import IntegrityError, OperationalError
from django.shortcuts import redirect, render # 最初これだけ
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import TemplateView, FormView
from . import tweepy
from .models import Tweets, TweetKeyword
from .forms import GetTweetForm, AnalysisForm, RegisterKeywordForm
import re
import emoji
from datetime import timedelta
from django.utils.timezone import localtime
import pandas as pd
from .graphs import Plot_Graph
from datetime import timedelta

# Create your views here.
class Index(TemplateView):
    template_name = "tweepy_test/index.html"

class SearchCriteria(FormView):
    form_class    = GetTweetForm
    template_name = "tweepy_test/search_criteria.html"

"""
class RegisterKeywordView(CreateView):
    model  = TweetKeyword
    fields = '__all__'
    success_url = reverse_lazy('index')
"""

# 全角スペースが入力されてくることへの対抗措置
def register_keyword(request):
    template_name = 'tweepy_test/tweetkeyword_form.html'
    ctx = {}

    # 単なるアクセスならフォームを返す
    if request.method == 'GET':
        form = RegisterKeywordForm
        ctx['form'] = form
        return render(request, template_name, ctx)
    # キーワードが入力されたら以下の処理
    if request.method == 'POST':
        keyword_form = RegisterKeywordForm(request.POST)
        if keyword_form.is_valid():
            keyword = keyword_form.cleaned_data
            keyword = keyword['keyword']
            if "　" in keyword:
                keyword = keyword.replace("　"," ")
            TweetKeyword.objects.create(
                keyword = str(keyword)
            )

            ctx = {
                'form' :RegisterKeywordForm,
                'keyword' :keyword,
            }
            return render(request, template_name, ctx)
        
        else:
            # エラーだったら入力した内容を返す
            ctx['form'] = keyword_form
            return render(request, template_name, ctx)



def get_tweets_view(request):
    template_name = 'tweepy_test/twitter_get.html'
    ctx = {}
    
    # 単なるアクセスならフォームを返す
    if request.method == "GET":
        form = GetTweetForm
        ctx['form'] = form
        return render(request, template_name, ctx)
    
    # フォームからデータ送信されてきたらTwitter APIを使う
    if request.method == "POST":
        # フォームのPOST情報を取得
        search_form = GetTweetForm(request.POST)
        if search_form.is_valid():
            search_criteria = search_form.cleaned_data
            # get_tweet()に渡す引数を準備
            searchkey = search_criteria['keyword']
            location  = ""
            item_num  = 1
            # ツイートを取得する関数を呼び出し
            tweet_data = tweepy.get_tweets(searchkey, location, item_num)

            # 取得したツイートデータをDBに保存 & 保存した数を数えて表示する
            tweet_count = 0
            for i in range(len(tweet_data)):
                try:
                    Tweets.objects.create(
                        keyword    =str(tweet_data[i][0]),
                        tweet_id   =str(tweet_data[i][1]),
                        user_id    =str(tweet_data[i][2]),
                        user_name  =str(tweet_data[i][3]),
                        text       =str(tweet_data[i][4]),
                        favorite   =int(tweet_data[i][5]),
                        retweet    =int(tweet_data[i][6]),
                        created_at =tweet_data[i][7],
                        )
                    tweet_count += 1
                except IntegrityError:
                    pass

            ctx = {
                'form': search_form,
                'searchkey': searchkey,
                'tweet_count': tweet_count, 
                }

            return render(request, 'tweepy_test/search_criteria.html', ctx)
        
        else:
            ctx['form'] = search_form
            return render(request, template_name, ctx)


class TweetAnalysis(FormView):
    form_class    = AnalysisForm
    template_name = 'tweepy_test/twitter_analysis.html'

    def form_valid(self, form):
        # 以下はグラフを表示するためのコード
        criteria  = form.cleaned_data
        keyword   = criteria['keyword']
        start_day = criteria['start_day']
        end_day   = criteria['end_day']
        # キーワードに完全一致して、、かつツイート日時が指定期間のツイートだけを抽出してくる（filterのand条件の記載方法）
        # qs = Tweets.objects.filter(keyword=keyword)
        qs = Tweets.objects.filter(keyword=keyword, created_at__range=[start_day, end_day + timedelta(days=1)])

        # 該当キーワードのツイート情報を一時的に格納し、日付情報などを整理する
        dataf = pd.DataFrame({
            'tweet_time':[],
            'tweet_count':[],
            'favorite':[],
            'retweet':[],
        })
        # データフレームに1行ずつインサートしていく（1はツイート数。1行1ツイートのため1としている）
        for i in range(len(qs)):
            tweet_data   = qs[i] 
            dataf.loc[i] = [localtime(tweet_data.created_at), 1, tweet_data.favorite, tweet_data.retweet]
        # ツイート日時の情報を日付に直す
        dataf['tweet_time'] = pd.to_datetime(dataf['tweet_time']).dt.date

        # グラフに表示する「対象期間の日数」を指定する
        N = (end_day - start_day).days + 1
        # 指定期間の日付をキーに辞書を作り、ツイート数といいね&リツイート数をリストで格納する → ('日付':(ツイート数, いいね&リツイート数))
        tweet_days = {}
        for i in range(N):
            date = start_day + timedelta(i)
            tweet_days[date] = [0, 0]
        
        # tweet_daysの日付に合致するところの[ツイート数, いいね&リツイート数を更新する]
        # iterrowsにするとデータフレームを1行ずつ繰り返し処理できるようになる
        # (インデックス番号, (tweet_time, tweet_count, favorite, retweet))という構造になる
        for data in dataf.iterrows():
            if data[1][0] in tweet_days:    # 上記のtweet_timeがtweet_daysの中にあるかで条件分岐
                # data[1][0]でようやくtweet_timeに行きつく→リストになっているため、そのうち１番目と２番目を更新する
                tweet_days[data[1][0]][0] += data[1][1]
                tweet_days[data[1][0]][1] += (data[1][2] + data[1][3])
        
        # グラフのx軸とy軸を作る
        tweet_date       = []
        tweet_count      = []
        favorite_retweet = []
        for key, value in tweet_days.items():
            value = list(value)
            tweet_date.append(key)
            tweet_count.append(value[0])
            favorite_retweet.append(value[1])
        # グラフを作成する関数を呼び出す
        chart = Plot_Graph(tweet_date, tweet_count, favorite_retweet)

        # いいね数でランキングして上位5つのテキストを表示する
        good_ranking = []
        for i in range(len(qs)):
            tweet_data2 = qs[i]
            good_ranking.append([tweet_data2.favorite, "【{0}いいね】 / {1} / {2}".format(tweet_data2.favorite, tweet_data2.user_name, localtime(tweet_data2.created_at).strftime('%Y-%m-%d %H:%M')), tweet_data2.text])

        # リストの1番目にある「いいね数」で降順に並び替える＝ランキング化        
        good_ranking.sort(reverse=True)
        # テンプレートに渡すのは5つだけにするため新たにリストに格納する（リスト形式にしないとテンプレート側で扱えない）
        top_tweet = []
        for i in range(5):
            top_tweet.append([good_ranking[i][1], good_ranking[i][2]])

        y = list(dataf['tweet_time'])

        ctxt  = self.get_context_data(chart=chart, form=form, top_tweet=top_tweet, y=y)
        return self.render_to_response(ctxt)


        



"""
# 一旦モデルには入れずにダイレクト表示してみる point_radius:[140 36 30km]
def TwitterAnalysis(request):
    searchkey = "めざましテレビ"
    location  = "point_radius:[140 36 30km]"
    search ="{0} {1}".format(searchkey, location)
    item_num = 3
    
    # tweet_data = tweepy.get_tweets(search, item_num)

    ctxt = {
        'tweet_id': tweet_data[0][0],
        'tweet_text': tweet_data[0][3],
    }

    return render(request, "tweepy_test/twitter_analysis.html", ctxt)


class TwitterAnalysis2(TemplateView):
    template_name = "tweepy_test/twitter_analysis.html"

    def get_context_data(self):
        ctxt = super().get_context_data()

        searchkey = "めざましテレビ"
        location  = ""
        search ="{0} {1}".format(searchkey, location)
        item_num = 3
        
        # tweet_data = tweepy.get_tweets(search, item_num)
        
        ctxt = {
            'tweet_id': tweet_data[0][0],
            'tweet_text': tweet_data[0][3],
        }

        return ctxt


class TwitterAnalysis3(TemplateView):
    template_name = "tweepy_test/twitter_analysis.html"
    model = Tweets

    searchkey = "めざまし"
    location  = ""
    search ="{0} {1}".format(searchkey, location)
    item_num = 3
    
    # tweet_data = tweepy.get_tweets(search, item_num)

    # 取得したツイートデータをDBに保存
    for i in range(len(tweet_data)):
        try:
            Tweets.objects.create(
                tweet_id   =str(tweet_data[i][0]),
                user_id    =str(tweet_data[i][1]),
                # user_name  =str(tweet_data[i][2]), 絵文字がダメなのかも
                # text       =str(tweet_data[i][3]),
                favorite   =int(tweet_data[i][4]),
                retweet    =int(tweet_data[i][5]),
                created_at =tweet_data[i][6],
                )
        except IntegrityError:
            pass

    def get_context_data(self):
        ctxt = super().get_context_data()
        # モデルの1行目をとりあえず表示する
        qs   = Tweets.objects.all()
        ctxt = {
            'tweet_set': qs
            #'tweet_text': qs[3],
        }

        return ctxt

class GetTweetView(FormView):
    form_class    = GetTweetForm
    template_name = "tweepy_test/twitter_get.html"
    success_url = reverse_lazy('searchcriteria')

    def form_valid(self, form):
        # formからデータを受け取る
        search_criteria = form.cleaned_data
        searchkey       = search_criteria['searchkey']
        location        = ""
        
        # get_tweet()に渡す引数を準備
        search     ="{0} {1}".format(searchkey, location)
        item_num   = 3
        
        tweet_data = tweepy.get_tweets(search, item_num)
        
        # 取得したツイートデータをDBに保存 & 保存した数を数えて表示する
        tweet_count = 0
        
        for i in range(len(tweet_data)):
            try:
                Tweets.objects.create(
                    tweet_id   =str(tweet_data[i][0]),
                    user_id    =str(tweet_data[i][1]),
                    # user_name  =str(tweet_data[i][2]), 絵文字がダメなのかも
                    # text       =str(tweet_data[i][3]),
                    favorite   =int(tweet_data[i][4]),
                    retweet    =int(tweet_data[i][5]),
                    created_at =tweet_data[i][6],
                    )
                tweet_count += 1
            except IntegrityError:
                pass
        # ここで返したコンテキスト変数は、同じtwitter_get.htmlでなら使える
        ctxt = self.get_context_data(form=form, tweet_count=tweet_count)
        return self.render_to_response(ctxt)


def get_tweets_view(request):
    template_name = 'tweepy_test/twitter_get.html'
    ctx = {}
    if request.method == "GET":
        form = GetTweetForm
        ctx['form'] = form
        return render(request, template_name, ctx)
    
    if request.method == "POST":
        search_form = GetTweetForm(request.POST)
        if search_form.is_valid():
            search_criteria = search_form.cleaned_data
            searchkey       = search_criteria['searchkey']
            location        = "point_radius:[140 36 30km]"
            # get_tweet()に渡す引数を準備
            search     ="{0} {1}".format(searchkey, location)
            item_num   = 10
            # ツイートを取得する関数を呼び出し
            tweet_data = tweepy.get_tweets(search, item_num)

            # 取得したツイートデータをDBに保存 & 保存した数を数えて表示する
            tweet_count = 0
            for i in range(len(tweet_data)):
                try:
                    user_name = re.sub(emoji.get_emoji_regexp(), "", tweet_data[i][2]) 
                    text      = re.sub(emoji.get_emoji_regexp(), "", tweet_data[i][3])
                    Tweets.objects.create(
                        tweet_id   =str(tweet_data[i][0]),
                        user_id    =str(tweet_data[i][1]),
                        user_name  =str(user_name),
                        text       =str(text),
                        favorite   =int(tweet_data[i][4]),
                        retweet    =int(tweet_data[i][5]),
                        created_at =tweet_data[i][6],
                        )
                    tweet_count += 1
                except OperationalError:
                    try:
                        Tweets.objects.create(
                            tweet_id   =str(tweet_data[i][0]),
                            user_id    =str(tweet_data[i][1]),
                            favorite   =int(tweet_data[i][4]),
                            retweet    =int(tweet_data[i][5]),
                            created_at =tweet_data[i][6],
                            )
                        tweet_count += 1
                    except IntegrityError:
                        pass
                except IntegrityError:
                    pass

            ctx = {
                'form': search_form,
                'searchkey': searchkey,
                'tweet_count': tweet_count, 
                }

            return render(request, 'tweepy_test/search_criteria.html', ctx)
        
        else:
            ctx['form'] = search_form
            return render(request, template_name, ctx)
"""


