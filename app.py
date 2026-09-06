import streamlit as st
import yfinance as yf
import requests
import time
import pandas as pd

st.set_page_config(page_title="高配当株 8ステップ分析ツール", layout="wide")

st.title("📈 高配当株 8ステップ総合診断ツール")
st.caption("個別銘柄の深掘り診断 ＆ 注目銘柄の一覧リスト比較")

# 海外IP制限回避の設定
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
})

# 主要銘柄の辞書（コード：会社名）
STOCK_NAMES = {
    "1928": "大和ハウス工業",
    "1925": "積水ハウス",
    "2914": "日本たばこ産業 (JT)",
    "2502": "アサヒグループHD",
    "2503": "キリンHD",
    "4502": "武田薬品工業",
    "8316": "三井住友フィナンシャルグループ",
    "8593": "三菱HCキャピタル",
    "9432": "日本電信電話 (NTT)",
    "7203": "トヨタ自動車",
    "8306": "三菱UFJフィナンシャル・グループ",
    "9104": "商船三井",
}

# 画面をタブで切り分ける（個別診断 ＆ 一覧リスト）
tab1, tab2 = st.tabs(["🔍 個別銘柄をくわしく診断", "📋 注目銘柄の一覧リスト比較"])

# ==========================================
# タブ1：個別銘柄診断
# ==========================================
with tab1:
    st.subheader("個別銘柄 8ステップ詳細診断")
    ticker_code = st.text_input("銘柄コードを入力してください（例: 8316, 8593, 1928）", value="8316")

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
            col1, col2, col3 = st.columns(3)
            col1.metric("現在株価", f"{price:,.0f} 円" if price else "---")
            col2.metric("配当利回り", f"{div_yield:.2f}%" if div_yield else "---")
            col3.metric("PBR", f"{pbr:.2f}倍" if pbr else "---")

            st.markdown("---")
            st.subheader("📋 8ステップ詳細判定")

            # 1. 配当利回り
            if div_yield >= 2.5:
                st.success(f"1. 配当利回り: 🟢 {div_yield:.2f}% (基準2.5%以上クリア)")
            else:
                st.warning(f"1. 配当利回り: 🟡 {div_yield:.2f}% (2.5%未満)")

            # 2. 配当性向
            if 0 < payout_ratio <= 60:
                st.success(f"2. 配当性向: 🟢 {payout_ratio:.1f}% (60%以下で健全)")
            elif payout_ratio > 60:
                st.error(f"2. 配当性向: 🔴 {payout_ratio:.1f}% (60%超過・減配注意)")
            else:
                st.info("2. 配当性向: ◯ データなし")

# ==========================================
# タブ2：一覧リスト比較
# ==========================================
with tab2:
    st.subheader("📋 注目高配当株の自動一覧リスト")
    st.caption("登録されている主要銘柄の現在の株価・配当利回り・PBRをまとめて比較します。")

    if st.button("🔄 一覧データを一括取得する", type="primary"):
        with st.spinner("全銘柄のデータを取得中...（少し時間がかかります）"):
            table_data = []
            for code, company_name in STOCK_NAMES.items():
                try:
                    s = yf.Ticker(f"{code}.T", session=session)
                    inf = s.info or {}
                    p = inf.get('currentPrice') or inf.get('regularMarketPrice') or 0
                    r_div = inf.get('dividendYield') or 0
                    d_y = r_div if r_div > 1 else r_div * 100
                    p_b = inf.get('priceToBook') or 0
                    
                    table_data.append({
                        "銘柄コード": code,
                        "銘柄名": company_name,
                        "現在株価 (円)": f"{p:,.0f}" if p else "---",
                        "配当利回り (%)": f"{d_y:.2f}%" if d_y else "---",
                        "PBR (倍)": f"{p_b:.2f}" if p_b else "---"
                    })
                except Exception:
                    table_data.append({
                        "銘柄コード": code,
                        "銘柄名": company_name,
                        "現在株価 (円)": "取得失敗",
                        "配当利回り (%)": "---",
                        "PBR (倍)": "---"
                    })
                time.sleep(0.3) # サーバー負荷軽減の待機
            
            # データフレーム（表）に変換して表示
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)
            st.success("✨ 一覧データの取得が完了しました！")
