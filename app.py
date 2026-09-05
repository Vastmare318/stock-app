import time
import requests
import streamlit as st
import yfinance as yf

# スマホ表示用の基本設定
st.set_page_config(page_title="高配当株 8ステップ分析ツール", page_icon="📈", layout="centered")

st.title("📈 高配当株 8ステップ自動診断")
st.caption("累計配当・減配リスクを見極める分析ツール")

# 海外IP制限回避の設定
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

# 銘柄コード入力フォーム
ticker_code = st.text_input("銘柄コードを入力してください（例: 8316, 8593）", value="8316")

if st.button("🔍 診断を実行する", type="primary"):
    with st.spinner("データを取得・解析中..."):
        symbol = f"{ticker_code}.T"
        stock = yf.Ticker(symbol, session=session)
        
        info = {}
        for _ in range(3):
            try:
                info = stock.info or {}
                if info and 'longName' in info:
                    break
            except Exception:
                pass
            time.sleep(0.5)

        name = info.get('longName') or info.get('shortName') or f"銘柄コード: {ticker_code}"
        price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
        div_yield = (info.get('dividendYield') or 0) * 100
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
            st.info("2. 配当性向: ⚪ データなし")

        # 財務データ取得
        try:
            balance = stock.balance_sheet
            financials = stock.financials
            cashflow = stock.cashflow
        except Exception:
            balance, financials, cashflow = None, None, None

        # 3. 自己資本比率
        try:
            if balance is not None and not balance.empty and 'Total Stockholder Equity' in balance.index and 'Total Assets' in balance.index:
                equity = balance.loc['Total Stockholder Equity'].iloc[0]
                assets = balance.loc['Total Assets'].iloc[0]
                equity_ratio = (equity / assets) * 100
                if equity_ratio >= 40 or 'Financial' in sector or 'Bank' in sector:
                    st.success(f"3. 自己資本比率: 🟢 {equity_ratio:.1f}% (健全)")
                    clear_count += 1
                else:
                    st.warning(f"3. 自己資本比率: 🟡 {equity_ratio:.1f}% (40%未満)")
            else:
                st.info("3. 自己資本比率: ⚪ 金融/データ制限につき個別確認要")
                clear_count += 1
        except Exception:
            st.info("3. 自己資本比率: ⚪ 判定スキップ")

        # 4. 営業CF
        try:
            if cashflow is not None and not cashflow.empty and 'Operating Cash Flow' in cashflow.index:
                op_cf = cashflow.loc['Operating Cash Flow'].iloc[0]
                if op_cf > 0:
                    st.success(f"4. 営業CF: 🟢 プラス ({op_cf/100000000:,.1f} 億円)")
                    clear_count += 1
                else:
                    st.error("4. 営業CF: 🔴 マイナス (本業で現金減少)")
            else:
                st.info("4. 営業CF: ⚪ データ保留")
                clear_count += 1
        except Exception:
            st.info("4. 営業CF: ⚪ 判定スキップ")

        # 5. 売上高成長
        try:
            if financials is not None and not financials.empty and 'Total Revenue' in financials.index:
                rev_recent = financials.loc['Total Revenue'].iloc[0]
                rev_old = financials.loc['Total Revenue'].iloc[-1]
                if rev_recent >= rev_old:
                    st.success(f"5. 売上高成長: 🟢 増加・維持傾向 ({rev_recent/100000000:,.1f} 億円)")
                    clear_count += 1
                else:
                    st.warning("5. 売上高成長: 🟡 減少傾向")
            else:
                st.info("5. 売上高成長: ⚪ データ保留")
                clear_count += 1
        except Exception:
            st.info("5. 売上高成長: ⚪ 判定スキップ")

        # 6. EPS成長
        try:
            if financials is not None and not financials.empty and 'Basic EPS' in financials.index:
                eps_recent = financials.loc['Basic EPS'].iloc[0]
                eps_old = financials.loc['Basic EPS'].iloc[-1]
                if eps_recent >= eps_old and eps_recent > 0:
                    st.success(f"6. EPS(1株利益): 🟢 成長傾向 ({eps_recent:.1f} 円)")
                    clear_count += 1
                else:
                    st.warning("6. EPS(1株利益): 🟡 減少または赤字")
            else:
                st.info("6. EPS(1株利益): ⚪ データ保留")
                clear_count += 1
        except Exception:
            st.info("6. EPS(1株利益): ⚪ 判定スキップ")

        # 7. PBR
        if 0 < pbr <= 1.0:
            st.success(f"7. PBR (割安度): 🟢 {pbr:.2f}倍 (1.0倍以下・割安)")
            clear_count += 1
        elif pbr > 1.0:
            st.warning(f"7. PBR (割安度): 🟡 {pbr:.2f}倍 (1.0倍超過)")
        else:
            st.info("7. PBR (割安度): ⚪ データなし")

        # 総合判定結果
        st.markdown("---")
        st.subheader("🎯 総合評価")
        st.write(f"**クリア数: {clear_count} / 7 項目**")
        if clear_count >= 5:
            st.balloons()
            st.success("🌟 高評価！累計配当銘柄として期待できます。")
        else:
            st.warning("🔍 慎重に検討（一部基準を満たしていません）。")
