import streamlit as st
import yfinance as yf
import pandas as pd

# =========================================================
# 基本設定
# =========================================================

st.set_page_config(
    page_title="高配当株AI秘書",
    page_icon="📈",
    layout="wide"
)

st.title("📈 高配当株AI秘書")
st.caption("保有銘柄の確認・高配当株スクリーニング・個別診断（財務・配当健全性チェック対応）")

# =========================================================
# 保有銘柄（初期データ）
# =========================================================

PORTFOLIO = {
    "1429": {"name": "日本アクア", "shares": 100},
    "1928": {"name": "積水ハウス", "shares": 5},
    "2914": {"name": "JT", "shares": 20},
    "4596": {"name": "窪田製薬HD", "shares": 10},
    "5016": {"name": "JX金属", "shares": 1},
    "5401": {"name": "日本製鉄", "shares": 1},
    "5802": {"name": "住友電工", "shares": 3},
    "7794": {"name": "イーディーピー", "shares": 8},
    "8306": {"name": "三菱UFJ", "shares": 1},
    "8593": {"name": "三菱HCキャピタル", "shares": 10},
}

# =========================================================
# URL生成
# =========================================================

def yahoo_url(code):
    return f"https://finance.yahoo.co.jp/quote/{code}.T"

def irbank_url(code):
    return f"https://irbank.net/{code}"

# =========================================================
# Yahoo Finance等からのデータ取得
# =========================================================

@st.cache_data(ttl=1800)
def get_stock_data(code):
    ticker = yf.Ticker(f"{code}.T")
    result = {
        "price": None,
        "market_cap": None,
        "yield": None,
        "dividend": None,
        "eps": None,
        "payout": None,
        "equity_ratio": None,
    }
    
    # 株価
    try:
        hist = ticker.history(period="5d", auto_adjust=False)
        if not hist.empty:
            result["price"] = float(hist["Close"].dropna().iloc[-1])
        else:
            result["price"] = ticker.fast_info.get("lastPrice")
    except Exception:
        pass

    # 財務・指標情報
    try:
        info = ticker.info
        result["market_cap"] = info.get("marketCap")
        
        y = info.get("dividendYield")
        if y is not None:
            if y < 1:
                y *= 100
            result["yield"] = y
            
        result["dividend"] = info.get("dividendRate")
        
        # EPSの複数キー取得対応
        result["eps"] = info.get("trailingEps") or info.get("epsTrailingTwelveMonths")
        
        payout = info.get("payoutRatio")
        if payout is not None:
            if payout < 1:
                payout *= 100
            result["payout"] = payout
            
        result["equity_ratio"] = info.get("debtToEquity")
    except Exception:
        pass

    # EPSと配当から配当性向の補完
    try:
        if result["dividend"] and result["eps"] and not result["payout"] and result["eps"] > 0:
            result["payout"] = (result["dividend"] / result["eps"]) * 100
    except Exception:
        pass

    return result

# =========================================================
# 表示用フォーマット関数
# =========================================================

def yen(value):
    if value is None:
        return "-"
    try:
        return f"{value:,.0f}円"
    except:
        return "-"

def percent(value):
    if value is None:
        return "-"
    try:
        return f"{value:.2f}%"
    except:
        return "-"

def market_cap_str(value):
    if value is None:
        return "-"
    try:
        if value >= 1_000_000_000_000:
            return f"{value / 1_000_000_000_000:.2f}兆円"
        if value >= 100_000_000:
            return f"{value / 100_000_000:.0f}億円"
        return f"{value:,.0f}円"
    except:
        return "-"

# =========================================================
# アプリ画面の構成
# =========================================================

st.header("🏠 ダッシュボード")
st.write("登録されている保有銘柄のサマリーと運用状況です。")

# サマリーデータ作成
with st.spinner("保有銘柄の最新情報を取得しています..."):
    portfolio_data = []
    for code, data in PORTFOLIO.items():
        stock = get_stock_data(code)
        price = stock["price"]
        shares = data["shares"]
        dividend = stock["dividend"]
        
        value = price * shares if price is not None else None
        annual_dividend = dividend * shares if dividend is not None else None
        
        portfolio_data.append({
            "code": code,
            "name": data["name"],
            "shares": shares,
            "price": price,
            "value": value,
            "yield": stock["yield"],
            "dividend": dividend,
            "annual_dividend": annual_dividend,
            "market_cap": stock["market_cap"],
            "eps": stock["eps"],
            "payout": stock["payout"],
        })
        
    df_portfolio = pd.DataFrame(portfolio_data)

# 上部メトリクスカード
total_value = df_portfolio["value"].sum(skipna=True)
annual_dividend_total = df_portfolio["annual_dividend"].sum(skipna=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("保有銘柄数", f"{len(PORTFOLIO)}銘柄")
with col2:
    st.metric("株式評価額", yen(total_value))
with col3:
    st.metric("年間予想配当", yen(annual_dividend_total))
with col4:
    st.metric("月平均配当", yen(annual_dividend_total / 12))

st.divider()

# =========================================================
# メニュー（タブ切り替え）
# =========================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "💰 保有銘柄一覧", 
    "📊 個別診断・健全性チェック", 
    "🔎 高配当スクリーニング条件", 
    "📚 IR・企業情報"
])

# ---------------------------------------------------------
# Tab 1: 保有銘柄一覧
# ---------------------------------------------------------
with tab1:
    st.subheader("💰 保有銘柄リスト")
    for _, row in df_portfolio.iterrows():
        code = row["code"]
        name = row["name"]
        with st.container(border=True):
            c_a, c_b = st.columns([2, 5])
            with c_a:
                st.markdown(f"### {name}")
                st.caption(f"証券コード：{code}")
            with c_b:
                sc1, sc2, sc3, sc4 = st.columns(4)
                with sc1:
                    st.metric("株価", yen(row["price"]))
                with sc2:
                    st.metric("保有株数", f"{int(row['shares'])}株")
                with sc3:
                    st.metric("配当利回り", percent(row["yield"]))
                with sc4:
                    st.metric("年間配当", yen(row["annual_dividend"]))
            
            bt1, bt2 = st.columns(2)
            with bt1:
                st.link_button("📊 Yahoo!ファイナンス", yahoo_url(code), use_container_width=True)
            with bt2:
                st.link_button("📚 IR BANK", irbank_url(code), use_container_width=True)

# ---------------------------------------------------------
# Tab 2: 個別診断・健全性チェック
# ---------------------------------------------------------
with tab2:
    st.subheader("📊 個別銘柄診断 & 健全性チェック")
    st.write("ご自身の投資ルール（EPS、配当性向、増減配トレンドなど）に照らし合わせて個別銘柄をチェックします。")
    
    selected_code = st.selectbox(
        "診断する銘柄を選択",
        list(PORTFOLIO.keys()),
        format_func=lambda x: f"{x}  {PORTFOLIO[x]['name']}"
    )
    
    if selected_code:
        data = get_stock_data(selected_code)
        name = PORTFOLIO[selected_code]["name"]
        
        st.markdown(f"### 🔍 {name} ({selected_code}) の診断結果")
        
        dc1, dc2, dc3, dc4 = st.columns(4)
        with dc1:
            st.metric("株価", yen(data["price"]))
        with dc2:
            st.metric("配当利回り", percent(data["yield"]))
        with dc3:
            st.metric("EPS", "-" if data["eps"] is None else f"{data['eps']:.2f}円")
        with dc4:
            st.metric("配当性向", percent(data["payout"]))
            
        st.markdown("#### 🛡️ 投資判断・健全性チェックリスト")
        
        # 簡易判定ロジックの表示
        payout_val = data["payout"]
        if payout_val is not None:
            if payout_val <= 50:
                payout_status = "🟢 健全水準（30〜50%の範囲内、または無理のない範囲）"
            else:
                payout_status = "⚠️ 要注意（配当性向が高めで負担が大きい可能性があります）"
        else:
            payout_status = "-（データ確認中）"

        checks = pd.DataFrame({
            "評価項目": [
                "時価総額規模",
                "EPS（10年トレンド）",
                "配当性向（目安:30〜50%）",
                "営業CF（黒字・増加傾向）",
                "自己資本比率（目安:40%以上）",
                "増配・減配トレンド",
                "5年・10年配当成長 / 増配率"
            ],
            "状態・目安": [
                "「3,000億円以上（できれば1兆円以上）」を推奨",
                "10年スパンで右肩上がりかIR BANK等で要確認",
                payout_status,
                "2期連続マイナスがないか要確認",
                "原則40%以上（銀行・商社・不動産は同業他社と比較）",
                "コロナ等の特殊要因による一時的減配は柔軟に許容",
                "過去の5年・10年平均増配率（%）・倍率を確認"
            ]
        })
        
        st.dataframe(checks, use_container_width=True, hide_index=True)
        
        st.divider()
        st.markdown("#### 🔗 公式情報・詳細リンク")
        l1, l2 = st.columns(2)
        with l1:
            st.link_button("📊 Yahoo!ファイナンスで見る", yahoo_url(selected_code), use_container_width=True)
        with l2:
            st.link_button("📚 IR BANKで財務を深掘り", irbank_url(selected_code), use_container_width=True)

# ---------------------------------------------------------
# Tab 3: 高配当スクリーニング条件
# ---------------------------------------------------------
with tab3:
    st.subheader("🔎 高配当株スクリーニングの全体像と基準")
    st.info("約4,000銘柄から以下の厳格な条件で絞り込むためのルール定義です。")
    
    criteria_df = pd.DataFrame({
        "条件項目": [
            "① 業界絞り込み",
            "② 配当利回り",
            "③ 連続増配年数",
            "④ 連続非減配年数",
            "⑤ 増減配実績",
            "⑥ 増配率",
            "⑦ 累進配当方針",
            "⑧ 財務・収益健全性"
        ],
        "設定基準・ルール": [
            "業界トップクラス・シェア上位に絞る",
            "2.5%以上",
            "長期で継続しているか確認",
            "非減配の継続年数を確認",
            "増配7回以上・減配1回以下（コロナ等の特例は柔軟判断）",
            "年率10%以上を目安",
            "公式IR・中期経営計画等で累進配当を宣言しているか確認",
            "EPS右肩上がり / 配当性向30〜50% / 営業CF連続プラス / 自己資本比率40%以上（業界特性を考慮）"
        ]
    })
    
    st.dataframe(criteria_df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# Tab 4: IR・企業情報
# ---------------------------------------------------------
with tab4:
    st.subheader("📚 保有銘柄のIRリンク集")
    for code, data in PORTFOLIO.items():
        st.markdown(f"### {code} {data['name']}")
        ic1, ic2 = st.columns(2)
        with ic1:
            st.link_button("Yahoo!ファイナンス", yahoo_url(code), use_container_width=True)
        with ic2:
            st.link_button("IR BANK", irbank_url(code), use_container_width=True)
        st.divider()

# =========================================================
# フッター
# =========================================================
st.caption("※株価・配当等のデータはYahoo Finance等から取得しています。実際の投資判断では最新の会社IRや中期経営計画等をご確認ください。")
