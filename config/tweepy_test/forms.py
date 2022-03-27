from django import forms
from .models import TweetKeyword
from django.core.exceptions import ValidationError

# キーワードを受け取るためのフォーム
class RegisterKeywordForm(forms.Form):
    keyword = forms.CharField(
        label="検索ワード")


class GetTweetForm(forms.Form):

    keyword = forms.ModelChoiceField(
        label="検索ワード",
        queryset=TweetKeyword.objects.all(),
        # widget=forms.RadioSelect,
        empty_label=None,)

    def clean(self):
        search_criteria = super().clean()     # criteriaは「判断基準」の意
        # vali = search_criteria['keyword']
        # バリデーションの設定は仮
        #if len(vali) >= 255:
        #    raise ValidationErr("文字数が多すぎます。")
        return search_criteria

# 日付をカレンダーで表示するためのクラス
class DateInput(forms.DateInput):
    input_type = 'date'


class AnalysisForm(forms.Form):
    
    keyword = forms.ModelChoiceField(
        label='検索ワード',
        queryset=TweetKeyword.objects.all(),
        #widget=forms.RadioSelect,
        # 空の選択肢を許すかどうか（デフォルトでは"-------"）
        empty_label=None,)

    start_day = forms.DateField(label="開始日", widget=DateInput())
    end_day = forms.DateField(label="終了日", widget=DateInput())

    def clean(self):
        period = super().clean()
        start_day = period["start_day"]
        end_day = period["end_day"]
        if start_day > end_day:
            raise ValidationError("開始日と終了日が前後しています。")
        return period
