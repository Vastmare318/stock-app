import time
import pandas as pd
import streamlit as st
import yfinance as yf

# =========================================================
# 基本設定
# =========================================================

st.set_page_config(page_title="高配当株AI秘書", page_icon="📈", layout="wide")

st.title("📈 高配当株AI秘書")
st.caption("保有銘柄の確認・高配当株スクリーニング・個別診断")

# =========================================================
# 保有銘柄
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
# URL
# =========================================================


def yahoo_url(code):
    return f"https://finance.yahoo.co.jp/quote/{code}.T"


def irbank_url(code):
    return f"https://irbank.net/{code}"


# =========================================================
# Yahoo Finance取得
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

    # -----------------------------
    # 株価
    # -----------------------------
    try:
        hist = ticker.history(period="5d", auto_adjust=False)
        if not hist.empty:
            result["price"] = float(hist["Close"].dropna().iloc[-1])
    except Exception:
        pass

    # -----------------------------
    # info
    # -----------------------------
    try:
        info = ticker.info
        result["market_cap"] = info.get("marketCap")
        result["yield"] = info.get("dividendYield")
        if result["yield"] is not None:
            # Yahooによって 0.034 / 3.4 の場合がある
            if result["yield"] < 1:
                result["yield"] *= 100
        result["dividend"] = info.get("dividendRate")
        result["eps"] = info.get("trailingEps")
        result["payout"] = info.get("payoutRatio")
        if result["payout"] is not None:
            if result["payout"] < 1:
                result["payout"] *= 100
        result["equity_ratio"] = info.get("debtToEquity")
    except Exception:
        pass

    return result


# =========================================================
# 数字表示
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


def market_cap(value):
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
# ダッシュボード
# =========================================================

st.header("🏠 ダッシュボード")

st.write("現在登録している保有銘柄です。")

# ---------------------------------------------------------
# サマリー
# ---------------------------------------------------------

with st.spinner("保有銘柄の情報を取得しています..."):
    portfolio_data = []
    for code, data in PORTFOLIO.items():
        stock = get_stock_data(code)
        price = stock["price"]
        shares = data["shares"]
        dividend = stock["dividend"]
        value = None
        annual_dividend = None

        if price is not None:
            value = price * shares

        if dividend is not None:
            annual_dividend = dividend * shares

        portfolio_data.append(
            {
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
            }
        )

    df_portfolio = pd.DataFrame(portfolio_data)

# =========================================================
# 上部カード
# =========================================================

total_value = df_portfolio["value"].sum(skipna=True)
annual_dividend_total = df_portfolio["annual_dividend"].sum(skipna=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("保有銘柄", f"{len(PORTFOLIO)}銘柄")

with col2:
    st.metric("株式評価額", yen(total_value))

with col3:
    st.metric("年間予想配当", yen(annual_dividend_total))

with col4:
    st.metric("月平均配当", yen(annual_dividend_total / 12))

st.divider()

# =========================================================
# 保有銘柄一覧
# =========================================================

st.subheader("💰 保有銘柄")

for _, row in df_portfolio.iterrows():
    code = row["code"]
    name = row["name"]
    with st.container(border=True):
        col1, col2 = st.columns([2, 5])
        with col1:
            st.markdown(f"### {name}")
            st.caption(f"証券コード：{code}")

        with col2:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("株価", yen(row["price"]))
            with c2:
                st.metric("保有株数", f"{int(row['shares'])}株")
            with c3:
                st.metric("配当利回り", percent(row["yield"]))
            with c4:
                st.metric("年間配当", yen(row["annual_dividend"]))

        b1, b2 = st.columns(2)
        with b1:
            st.link_button(
                "📊 Yahoo!ファイナンスを見る",
                yahoo_url(code),
                use_container_width=True,
            )
        with b2:
            st.link_button(
                "📚 IR BANKを見る", irbank_url(code), use_container_width=True
            )

# =========================================================
# 保有銘柄詳細データ
# =========================================================

st.divider()

st.subheader("📋 保有銘柄データ")

display_df = df_portfolio.copy()

display_df["株価"] = display_df["price"].apply(yen)
display_df["評価額"] = display_df["value"].apply(yen)
display_df["配当利回り"] = display_df["yield"].apply(percent)
display_df["年間配当"] = display_df["annual_dividend"].apply(yen)
display_df["時価総額"] = display_df["market_cap"].apply(market_cap)
display_df["EPS"] = display_df["eps"].apply(
    lambda x: "-" if pd.isna(x) else f"{x:.2f}円"
)
display_df["配当性向"] = display_df["payout"].apply(percent)

display_df = display_df[
    [
        "code",
        "name",
        "shares",
        "株価",
        "評価額",
        "配当利回り",
        "年間配当",
        "時価総額",
        "EPS",
        "配当性向",
    ]
]

display_df.columns = [
    "コード",
    "銘柄",
    "保有株数",
    "株価",
    "評価額",
    "配当利回り",
    "年間配当",
    "時価総額",
    "EPS",
    "配当性向",
]

st.dataframe(display_df, use_container_width=True, hide_index=True)

# =========================================================
# メニュー
# =========================================================

st.divider()

st.header("🔎 次にやること")

tab1, tab2, tab3 = st.tabs(["📊 個別診断", "💰 高配当スクリーニング", "📚 IR・企業情報"])

# =========================================================
# 個別診断
# =========================================================

with tab1:
    st.subheader("📊 個別銘柄診断")

    selected_code = st.selectbox(
        "銘柄を選択",
        list(PORTFOLIO.keys()),
        format_func=lambda x: f"{x}  {PORTFOLIO[x]['name']}",
    )

    if selected_code:
        data = get_stock_data(selected_code)

        st.markdown(f"## {PORTFOLIO[selected_code]['name']} ({selected_code})")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric("株価", yen(data["price"]))

        with c2:
            st.metric("配当利回り", percent(data["yield"]))

        with c3:
            st.metric(
                "EPS",
                "-" if data["eps"] is None else f"{data['eps']:.2f}円",
            )

        with c4:
            st.metric("配当性向", percent(data["payout"]))

        st.divider()

        st.link_button("📊 Yahoo!ファイナンス", yahoo_url(selected_code))

        st.link_button("📚 IR BANK", irbank_url(selected_code))

# =========================================================
# 高配当スクリーニング
# =========================================================

with tab2:
    st.subheader("💰 高配当株スクリーニング")

    st.info(
        "ここは次の段階で、JPXの約4,000銘柄を対象に "
        "時価総額・配当利回り・増配・配当成長・EPS・"
        "配当性向・営業CF・自己資本比率・33業種比較などを "
        "自動判定する機能にします。"
    )

    st.markdown("### 現在のスクリーニング条件")

    conditions = pd.DataFrame(
        {
            "条件": [
                "配当利回り",
                "時価総額",
                "増配回数",
                "通常の減配",
                "5年配当成長",
                "10年配当成長",
                "EPS",
                "配当性向",
                "営業CF",
                "自己資本比率",
            ],
            "基準": [
                "2.5%以上",
                "3,000億円以上を優先・1兆円以上を最優先",
                "7回以上を優先",
                "1回以下",
                "年率10%以上を目安",
                "年率10%以上を目安",
                "10年で右肩上がりを確認",
                "30～50%を基本",
                "プラスを基本",
                "40%以上を基本",
            ],
        }
    )

    st.dataframe(conditions, use_container_width=True, hide_index=True)

    st.warning(
        "JPX銘柄CSVをアップロードするだけで終わらず、"
        "次の段階ではアップロード後に自動で候補銘柄を取得して、"
        "S/A/B/C判定まで行うようにします。"
    )

# =========================================================
# IR・企業情報
# =========================================================

with tab3:
    st.subheader("📚 保有銘柄のIR・企業情報")

    for code, data in PORTFOLIO.items():
        st.markdown(f"### {code} {data['name']}")

        c1, c2 = st.columns(2)

        with c1:
            st.link_button(
                "Yahoo!ファイナンス", yahoo_url(code), use_container_width=True
            )

        with c2:
            st.link_button(
                "IR BANK", irbank_url(code), use_container_width=True
            )

        st.divider()

# =========================================================
# フッター
# =========================================================

st.caption(
    "※株価・配当等のデータはYahoo Finance等から取得しています。"
    "実際の投資判断では最新の会社IRも確認してください。"
)
