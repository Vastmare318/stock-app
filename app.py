import pandas as pd
import streamlit as st

st.set_page_config(page_title="銘柄一覧アプリ", layout="wide")

st.title("📊 銘柄管理ダッシュボード")

# サンプルデータの作成
# ※ 実際のアプリに合わせて、保有株数、評価額、利回り、年間配当、外部サイトURLのデータを設定してください
data = {
    "銘柄名": [
        "1429: 日本アクア",
        "1928: 積水ハウス",
        "2914: JT",
        "4596: 窪田製薬HD",
        "5016: JX金属",
        "5401: 日本製鉄",
        "5802: 住友電工",
        "7794: イーディーピー",
        "8306: 三菱UFJ",
        "8593: 三菱HCキャピタル",
    ],
    "株数": [
        "100株",
        "5株",
        "20株",
        "10株",
        "1株",
        "1株",
        "3株",
        "8株",
        "1株",
        "10株",
    ],
    "評価額": [
        "80,800円",
        "16,845円",
        "138,860円",
        "660円",
        "3,555円",
        "686円",
        "6,633円",
        "8,040円",
        "3,714円",
        "13,785円",
    ],
    "利回り": [
        "4.33%",
        "4.33%",
        "3.92%",
        "nan%",
        "56.00%",
        "3.50%",
        "1.76%",
        "nan%",
        "2.58%",
        "3.77%",
    ],
    "年間配当": [
        "3,500円",
        "730円",
        "5,440円",
        "nan円",
        "20円",
        "24円",
        "117円",
        "nan円",
        "96円",
        "520円",
    ],
    "外部サイト": [
        "https://example.com/1429",
        "https://example.com/1928",
        "https://example.com/2914",
        "https://example.com/4596",
        "https://example.com/5016",
        "https://example.com/5401",
        "https://example.com/5802",
        "https://example.com/7794",
        "https://example.com/8306",
        "https://example.com/8593",
    ],  # 一番右に配置する外部サイトへのURL
}

df = pd.DataFrame(data)

st.subheader("📋 保管銘柄・指標一覧（右端のリンクから外部サイトへ移動できます）")

# st.dataframe を使って、一番右にリンクカラムを配置
st.dataframe(
    df,
    column_config={
        "銘柄名": st.column_config.TextColumn("銘柄名", width="medium"),
        "株数": st.column_config.TextColumn("株数", width="small"),
        "評価額": st.column_config.TextColumn("評価額", width="small"),
        "利回り": st.column_config.TextColumn("利回り", width="small"),
        "年間配当": st.column_config.TextColumn("年間配当", width="small"),
        # 1番右に配置し、クリックして飛べるようにする列
        "外部サイト": st.column_config.LinkColumn(
            "外部サイト",
            help="クリックすると外部サイトが開きます",
            display_text="🔗 サイトを開く",  # ボタンやテキストとして表示させる名前
            width="medium",
        ),
    },
    use_container_width=True,
    hide_index=True,
)
