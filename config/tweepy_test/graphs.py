from cgitb import handler
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import base64
from io import BytesIO

def Output_Graph():
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    img   = buffer.getvalue()
    graph = base64.b64encode(img)
    graph = graph.decode("utf-8")
    buffer.close()
    return graph


def Plot_Graph(x,y,y2):
    # 日本語を表示する設定
    plt.rcParams['font.family'] = 'Yu Gothic'
    plt.switch_backend("AGG")
    plt.figure(figsize=(8,3))
    plt.bar(x, y, width=0.5, color='skyblue', label='ツイート数')
    plt.plot(x, y2, color="deepskyblue", label='いいね&リツイート数')
    # 凡例を表示
    plt.legend()
    plt.tight_layout()
    # x軸の日付フォーマットを変更している。Macなら「%-m/%-d」だが、windowsなら
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%#m/%#d"))

    graph = Output_Graph()
    return graph