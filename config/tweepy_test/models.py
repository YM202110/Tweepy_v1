from django.db import models


class TweetKeyword(models.Model):
    keyword = models.CharField(
        'キーワード',
        blank=False,
        null=False,
        unique=False,
        max_length=190,
    )

    def __str__(self):
        return self.keyword


class Tweets(models.Model):
    keyword = models.CharField(
        "検索キーワード",
        max_length=190,
        blank=False,
        null=False,
        unique=False,
    )

    tweet_id = models.CharField(
        'ツイートID',
        # フォームから入力する際に入力必須にするかどうか
        max_length=190,
        blank=False,
        # nullをOKにするかどうかだがCharFieldだと空文字が入るからTrueにはしない
        null=False,
        unique=False,)
    
    user_id = models.CharField(
        'ユーザーID',
        max_length=190,
        unique=False,)
    
    user_name = models.CharField(
        'ユーザー名',
        max_length=190,
        unique=False,)
    
    text = models.TextField(
        'ツイート内容',
        blank=True,
        null=True,)
    
    favorite = models.PositiveIntegerField(
        verbose_name='いいね数',)

    retweet = models.PositiveIntegerField(
        verbose_name='リツイート数',)


    created_at = models.DateTimeField(
        verbose_name='ツイート日時',)
    
    loaded_at = models.DateTimeField(
        verbose_name='データ取得日',
        auto_now_add=True)
    
    # 複合ユニークの設定
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["keyword","tweet_id"],
                name = "tweet_unique"
            )
        ]

    # def __str__(self)により、管理画面に表示されるモデル内のデータを判別するための、名前を定義することができる    
    def __str__(self):
        return self.text[:10]

