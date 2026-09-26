import pandas as pd
import streamlit as st

st.set_page_config(page_title="銘柄一覧＆評価アプリ", layout="wide")

st.title("📊 銘柄管理・評価ダッシュボード（4,000銘柄対応版）")

# サンプルデータ（4,000銘柄を想定した構造。実際にはCSVやDBから読み込んでください）
# ここでは例として提示された銘柄を含めたサンプルデータを作成しています
raw_data = [
    {
        "銘柄": "1429: 日本アクア",
        "株数": 100,
        "評価額": 80800,
        "利回り": 4.33,
        "年間配当": 3500,
        "外部サイト": "https://example.com/1429",
    },
    {
        "銘柄": "1928: 積水ハウス",
        "株数": 5,
        "評価額": 16845,
        "利回り": 4.33,
        "年間配当": 730,
        "外部サイト": "https://example.com/1928",
    },
    {
        "銘柄": "2914: JT",
        "株数": 20,
        "評価額": 138860,
        "利回り": 3.92,
        "年間配当": 5440,
        "外部サイト": "https://example.com/2914",
    },
    {
        "銘柄": "4596: 窪田製薬HD",
        "株数": 10,
        "評価額": 660,
        "利回り": 0.0,
        "年間配当": 0,
        "外部サイト": "https://example.com/4596",
    },
    {
        "銘柄": "5016: JX金属",
        "株数": 1,
        "評価額": 3555,
        "利回り": 56.00,
        "年間配当": 20,
        "外部サイト": "https://example.com/5016",
    },
    {
        "銘柄": "5401: 日本製鉄",
        "株数": 1,
        "評価額": 686,
        "利回り": 3.50,
        "年間配当": 24,
        "外部サイト": "https://example.com/5401",
    },
    {
        "銘柄": "5802: 住友電工",
        "株数": 3,
        "評価額": 6633,
        "利回り": 1.76,
        "年間配当": 117,
        "外部サイト": "https://example.com/5802",
    },
    {
        "銘柄": "7794: イーディーピー",
        "株数": 8,
        "評価額": 8040,
        "利回り": 0.0,
        "年間配当": 0,
        "外部サイト": "https://example.com/7794",
    },
    {
        "銘柄": "8306: 三菱UFJ",
        "株数": 1,
        "評価額": 3714,
        "利回り": 2.58,
        "年間配当": 96,
        "外部サイト": "https://example.com/8306",
    },
    {
        "銘柄": "8593: 三菱HCキャピタル",
        "株数": 10,
        "評価額": 13785,
        "利回り": 3.77,
        "年間配当": 520,
        "外部サイト": "https://example.com/8593",
    },
]

df = pd.DataFrame(raw_data)

# --- 1. 評価（サマリー）機能 ---
st.subheader("📈 ポートフォリオ評価")
total_value = df["評価額"].sum()
total_dividend = df["年間配当"].sum()
avg_yield = (
    (df["年間配当"].sum() / df["評価額"].sum() * 100) if total_value > 0 else 0
)

col1, col2, col3 = st.columns(3)
col1.metric("総評価額", f"{total_value:,.0f} 円")
col2.metric("年間配当金合計", f"{total_dividend:,.0f} 円")
col3.metric("平均配当利回り", f"{avg_yield:.2f}%")

st.divider()

# --- 2. 4,000銘柄対応の絞り込み（検索・セレクトボックス）機能 ---
st.subheader("🔍 銘柄の絞り込み・検索")

col_search1, col_search2 = st.columns(2)

with col_search1:
  # テキストによるフリーワード検索
  search_query = st.text_input(
    "キーワード検索（銘柄名・コード）",
    placeholder="例: 1429, トヨタ, JT など...",
  )

with col_search2:
  # 4000銘柄からでも選びやすいセレクトボックス（プルダウン）絞り込み
  # リストが大量にある場合を考慮し、「すべて表示」を選択肢の先頭に入れます
  all_stocks_list = ["すべて選択（絞り込みなし）"] + df["銘柄"].tolist()
  selected_stock = st.selectbox("プルダウンから銘柄を選択", all_stocks_list)

# 絞り込み処理の適用
filtered_df = df.copy()

if search_query:
  filtered_df = filtered_df[
      filtered_df["銘柄"].str.contains(search_query, case=False, na=False)
  ]

if selected_stock and selected_stock != "すべて選択（絞り込みなし）":
  filtered_df = filtered_df[filtered_df["銘柄"] == selected_stock]

# --- 3. 表示用の数値フォーマット整形 ---
display_df = filtered_df.copy()
display_df["株数"] = display_df["株数"].astype(str) + "株"
display_df["評価額"] = display_df["評価額"].apply(lambda x: f"{x:,.0f}円")
display_df["利回り"] = display_df["利回り"].apply(
    lambda x: f"{x:.2f}%" if x > 0 else "nan%"
)
display_df["年間配当"] = display_df["年間配当"].apply(
    lambda x: f"{x:,.0f}円" if x > 0 else "nan円"
)

# --- 4. テーブル表示（一番右に外部サイトリンク） ---
st.write(f"該当件数: **{len(display_df)}** 銘柄")

st.dataframe(
    display_df,
    column_config={
        "銘柄": st.column_config.TextColumn("銘柄", width="medium"),
        "株数": st.column_config.TextColumn("株数", width="small"),
        "評価額": st.column_config.TextColumn("評価額", width="small"),
        "利回り": st.column_config.TextColumn("利回り", width="small"),
        "年間配当": st.column_config.TextColumn("年間配当", width="small"),
        # 一番右の列：クリックして外部サイトへ飛べるリンク
        "外部サイト": st.column_config.LinkColumn(
            "外部サイト",
            help="クリックして外部サイトを開く",
            display_text="🔗 サイトを開く",
            width="medium",
        ),
    },
    use_container_width=True,
    hide_index=True,
)
