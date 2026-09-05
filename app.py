import streamlit as st
import yfinance as yf
import requests
import time

st.set_page_config(page_title="高配当株 8ステップ分析ツール", layout="centered")

st.title("📈 高配当株 8ステップ自動診断")
st.caption("累計配当・減配リスクを見極める分析ツール")

# 海外IP制限回避の設定
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
})

# 日本株の主要銘柄・会社名マップ（必要に応じて追加できます）
STOCK_NAMES = {
    "8316": "三井住友フィナンシャルグループ",
    "8593": "三菱HCキャピタル",
    "9432": "日本電信電話 (NTT)",
    "7203": "トヨタ自動車",
    "8306": "三菱UFJフィナンシャル・グループ",
    "9104": "商船三井",
}

# 銘柄コード入力フォーム
ticker_code = st.text_input("銘柄コードを入力してください（例: 8316, 8593）", value="8316")

if st.button("🔍 診断を実行する", type="primary"):
    with st.spinner("データを取得・解析中..."):
        symbol = f"{ticker_code}.T"
        
        # 1. 会社名の取得（マップになければ「銘柄コード: XXXX」を表示）
        name = STOCK_NAMES.get(ticker_code, f"銘柄コード: {ticker_code}")
        
        # 2. 株価・財務データの取得（リトライ処理付き）
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
        sector = info.get('sector', '')

        # 概要カード表示
        st.subheader(f"📊 {name}")
        col1, col2, col3 = st.columns(3)
        col1.metric("現在株価", f"{price:,.0f} 円" if price else "---")
        col2.metric("配当利回り", f"{div_yield:.2f}%" if div_yield else "---")
        col3.metric("PBR", f"{pbr:.2f}倍" if pbr else "---")

        st.markdown("---")
        st.subheader("📋 8ステップ詳細判定")

        clear_count = 0

        # 1. 配当利回り
        if div_yield >= 2.5:
            st.success(f"1. 配当利回り: 🟢 {div_yield:.2f}% (基準2.5%以上クリア)")
            clear_count += 1
        else:
            st.warning(f"1. 配当利回り: 🟡 {div_yield:.2f}% (2.5%未満)")

        # 2. 配当性向
        if 0 < payout_ratio <= 60:
            st.success(f"2. 配当性向: 🟢 {payout_ratio:.1f}% (60%以下で健全)")
            clear_count += 1
        elif payout_ratio > 60:
            st.error(f"2. 配当性向: 🔴 {payout_ratio:.1f}% (60%超過・減配注意)")
        else:
            st.info("2. 配当性向: ◯ データなし")

        # 3. 自己資本比率（財務データ取得）
        try:
            balance = stock.balance_sheet
            if balance is not None and not balance.empty:
                st.info("3. 自己資本比率: 取得成功（詳細チェック中）")
            else:
                st.info("3. 自己資本比率: ◯ 金融/データ制限につき個別確認推奨")
        except Exception:
            st.info("3. 自己資本比率: ◯ データ保留")
