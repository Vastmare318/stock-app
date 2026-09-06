import streamlit as st
import yfinance as yf
import requests
import time
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="高配当株 8ステップ分析ツール", layout="wide")

st.title("📈 高配当株 ＆ 時価総額・財務分析ダッシュボード")
st.caption("個別銘柄の深掘り診断 ＆ みんかぶ・IR BANK風の一覧比較・グラフ表示")

# 海外IP制限回避の設定
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
})

# 主要銘柄の辞書（コード：会社名）
STOCK_NAMES = {
    "7203": "トヨタ自動車",
    "8306": "三菱UFJフィナンシャル・グループ",
    "8316": "三井住友フィナンシャルグループ",
    "2914": "日本たばこ産業 (JT)",
    "8058": "三菱商事",
    "8001": "伊藤忠商事",
    "9432": "日本電信電話 (NTT)",
    "8766": "東京海上ホールディングス",
    "1928": "大和ハウス工業",
    "1925": "積水ハウス",
    "8593": "三菱HCキャピタル",
    "9104": "商船三井",
}

# 画面をタブで切り分ける
tab1, tab2 = st.tabs(["🔍 個別銘柄をくわしく診断", "📋 一覧リスト・財務グラフ比較"])

# ==========================================
# タブ1：個別銘柄診断
# ==========================================
with tab1:
    st.subheader("個別銘柄 8ステップ詳細診断")
    ticker_code = st.text_input("銘柄コードを入力してください（例: 8316, 7203, 8593）", value="8316")

    if st.button("🔍 診断を実行する", type="primary"):
        with st.spinner("データを取得・解析中..."):
            symbol = f"{ticker_code}.T"
            name = STOCK_NAMES.get(ticker_code, f"銘柄コード: {ticker_code}")
            
            stock = yf.Ticker(symbol, session=session)
            info = {}
            for _ in range(3):
                try:
                    info = stock.info or {}
                    if info and 'currentPrice' in info:
                        break
                except Exception:
                    pass
                time.sleep(0.5)

            price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
            raw_div = info.get('dividendYield') or 0
            div_yield = raw_div if raw_div > 1 else raw_div * 100
            payout_ratio = (info.get('payoutRatio') or 0) * 100
            pbr = info.get('priceToBook') or 0

            # 概要カード表示
            st.subheader(f"📊 {name}")
            
            # みんかぶへのリンクボタン
            minkabu_url = f"https://minkabu.jp/stock/{ticker_code}"
            st.link_button("🌐 「みんかぶ」でこの銘柄のページを開く", minkabu_url)

            col1, col2, col3 = st.columns(3)
            col1.metric("現在株価", f"{price:,.0f} 円" if price else "---")
            col2.metric("配当利回り", f"{div_yield:.2f}%" if div_yield else "---")
            col3.metric("PBR", f"{pbr:.2f}倍" if pbr else "---")

            st.markdown("---")
            st.subheader("📊 過去の配当金推移（本のようなグラフ）")
            
            # 過去の配当金データを取得して年ごとに集計
            try:
                dividends = stock.dividends
                if not dividends.empty:
                    # インデックスを年単位に変換して合算
                    div_df = dividends.resample('YE').sum().reset_index()
                    div_df['Year'] = div_df['Date'].dt.strftime('%Y年')
                    
                    # 直近の数年間に絞る（例: 直近10年）
                    div_df = div_df.tail(10)
                    
                    # Plotlyで綺麗な棒グラフを作成
                    fig = go.Figure(data=[
                        go.Bar(
                            x=div_df['Year'],
                            y=div_df['Dividends'],
                            marker_color='#2ca02c',
                            text=div_df['Dividends'].round(2),
                            textposition='auto',
                        )
                    ])
                    fig.update_layout(
                        title=f"{name} の年間1株配当推移",
                        xaxis_title="年",
                        yaxis_title="配当金 (円)",
                        template="plotly_white",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("配当履歴データが見つかりませんでした。")
            except Exception as e:
                st.warning(lict := f"配当グラフの生成中にエラーが発生しました: {e}")

            st.markdown("---")
            st.subheader("📋 8ステップ詳細判定")

            if div_yield >= 2.5:
                st.success(f"1. 配当利回り: 🟢 {div_yield:.2f}% (基準2.5%以上クリア)")
            else:
                st.warning(f"1. 配当利回り: 🟡 {div_yield:.2f}% (2.5%未満)")

            if 0 < payout_ratio <= 60:
                st.success(f"2. 配当性向: 🟢 {payout_ratio:.1f}% (60%以下で健全)")
            elif payout_ratio > 60:
                st.error(f"2. 配当性向: 🔴 {payout_ratio:.1f}% (60%超過・減配注意)")
            else:
                st.info("2. 配当性向: ◯ データなし")

# ==========================================
# タブ2：一覧リスト ＆ 財務グラフ比較
# ==========================================
with tab2:
    st.subheader("📋 時価総額・財務データの一覧とグラフ比較")
    st.caption("主要銘柄の規模感や配当利回りを比較できます。")

    if st.button("🔄 データを一括取得・分析する", type="primary"):
        with st.spinner("全銘柄のデータを取得・計算中..."):
            table_data = []
            for code, company_name in STOCK_NAMES.items():
                try:
                    s = yf.Ticker(f"{code}.T", session=session)
                    inf = s.info or {}
                    p = inf.get('currentPrice') or inf.get('regularMarketPrice') or 0
                    r_div = inf.get('dividendYield') or 0
                    d_y = r_div if r_div > 1 else r_div * 100
                    p_b = inf.get('priceToBook') or 0
                    m_cap = inf.get('marketCap', 0) / 100000000
                    
                    table_data.append({
                        "コード": code,
                        "銘柄名": company_name,
                        "時価総額(億円)": round(m_cap, 1),
                        "現在株価(円)": round(p, 1),
                        "配当利回り(%)": round(d_y, 2),
                        "PBR(倍)": round(p_b, 2),
                        "みんかぶURL": f"https://minkabu.jp/stock/{code}"
                    })
                except Exception:
                    pass
                time.sleep(0.3)
            
            df = pd.DataFrame(table_data)
            st.session_state['stock_df'] = df

    if 'stock_df' in st.session_state:
        df = st.session_state['stock_df']
        
        st.markdown("### 📊 視覚的ビジュアル比較（グラフ）")
        g_col1, g_col2 = st.columns(2)
        
        with g_col1:
            st.markdown("##### 💰 配当利回りの比較 (%)")
            chart_div = df.set_index("銘柄名")["配当利回り(%)"]
            st.bar_chart(chart_div)
            
        with g_col2:
            st.markdown("##### 🏢 時価総額の比較 (億円)")
            chart_mcap = df.set_index("銘柄名")["時価総額(億円)"]
            st.bar_chart(chart_mcap)

        st.markdown("---")
        st.markdown("### 📋 詳細データ一覧表（みんかぶリンク付き）")
        st.dataframe(
            df.sort_values(by="時価総額(億円)", ascending=False),
            column_config={
                "みんかぶURL": st.column_config.LinkColumn("みんかぶリンク", display_text="ページを開く")
            },
            use_container_width=True
        )
        st.success("✨ 一覧データおよびグラフの生成が完了しました！")
