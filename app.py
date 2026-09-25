import math
import re
import time
import pandas as pd
import streamlit as st
import yfinance as yf

# =========================================================
# 基本設定
# =========================================================

st.set_page_config(
    page_title="日本株・高配当AI秘書",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# デザイン
# =========================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 34px;
        font-weight: 800;
        margin-bottom: 5px;
    }
    .sub-title {
        color: #666;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 定数・保有銘柄
# =========================================================

YAHOO_BASE = "https://finance.yahoo.co.jp/quote/"
IRBANK_BASE = "https://irbank.net/"

CAPITAL_INTENSIVE_SECTORS = {
    "銀行業",
    "証券、商品先物取引業",
    "不動産業",
    "卸売業",
}

MY_PORTFOLIO = {
    "1429": "日本アクア",
    "1928": "積水ハウス",
    "2914": "JT",
    "4596": "窪田製薬HD",
    "5016": "JX金属",
    "5401": "日本製鉄",
    "5802": "住友電工",
    "7794": "イーディーピー",
    "8306": "三菱UFJ",
    "8593": "三菱HCキャピタル",
}

# =========================================================
# ユーティリティ
# =========================================================


def clean_code(code):
    return str(code).strip().upper()


def valid_code(code):
    return bool(re.match(r"^\d{3,4}[A-Z]?$", clean_code(code)))


def yahoo_url(code):
    return f"{YAHOO_BASE}{clean_code(code)}.T"


def irbank_url(code):
    return f"{IRBANK_BASE}{clean_code(code)}"


def safe_float(value):
    try:
        if value is None:
            return None
        if isinstance(value, str):
            value = value.replace(",", "").replace("%", "")
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return None
        return result
    except Exception:
        return None


def fmt_money(value):
    value = safe_float(value)
    return "N/A" if value is None else f"{value:,.1f}"


def fmt_pct(value):
    value = safe_float(value)
    return "N/A" if value is None else f"{value:.1f}%"


def format_market_cap(value):
    value = safe_float(value)
    if value is None:
        return "N/A"
    if value >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.2f}兆円"
    if value >= 100_000_000:
        return f"{value / 100_000_000:.0f}億円"
    return f"{value:,.0f}円"


# =========================================================
# Yahoo Finance データ取得
# =========================================================


@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_data(code):
    code = clean_code(code)
    if not valid_code(code):
        return None
    symbol = f"{code}.T"
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="10y", auto_adjust=False)
        info = ticker.info
        return {"symbol": symbol, "hist": hist, "info": info}
    except Exception as e:
        return {
            "symbol": symbol,
            "hist": pd.DataFrame(),
            "info": {},
            "error": str(e),
        }


@st.cache_data(ttl=3600, show_spinner=False)
def get_dividend_history(code):
    code = clean_code(code)
    try:
        ticker = yf.Ticker(f"{code}.T")
        dividends = ticker.dividends
        if dividends is None or dividends.empty:
            return pd.DataFrame()
        df = dividends.to_frame("dividend")
        df.index = pd.to_datetime(df.index)
        df["year"] = df.index.year
        annual = df.groupby("year")["dividend"].sum().reset_index()
        return annual.sort_values("year")
    except Exception:
        return pd.DataFrame()


def get_current_eps(info):
    for x in [info.get("trailingEps"), info.get("epsTrailingTwelveMonths")]:
        val = safe_float(x)
        if val is not None:
            return val
    return None


def get_current_payout(info):
    x = safe_float(info.get("payoutRatio"))
    if x is not None:
        if x <= 1:
            x *= 100
        return x
    return None


def calculate_dividend_growth(annual):
    result = {
        "dividend_5y_multiple": None,
        "dividend_10y_multiple": None,
        "dividend_5y_cagr": None,
        "dividend_10y_cagr": None,
    }
    if annual is None or annual.empty:
        return result
    annual = annual.sort_values("year")
    latest_year = annual["year"].max()
    latest_rows = annual[annual["year"] == latest_year]
    if latest_rows.empty:
        return result
    current_dividend = safe_float(latest_rows["dividend"].iloc[0])
    if current_dividend is None or current_dividend <= 0:
        return result

    # 5年前
    old5 = annual[annual["year"] <= latest_year - 5]
    if not old5.empty:
        d5 = safe_float(old5.iloc[-1]["dividend"])
        if d5 and d5 > 0:
            result["dividend_5y_multiple"] = current_dividend / d5
            result["dividend_5y_cagr"] = (
                (current_dividend / d5) ** (1 / 5) - 1
            ) * 100

    # 10年前
    old10 = annual[annual["year"] <= latest_year - 10]
    if not old10.empty:
        d10 = safe_float(old10.iloc[-1]["dividend"])
        if d10 and d10 > 0:
            result["dividend_10y_multiple"] = current_dividend / d10
            result["dividend_10y_cagr"] = (
                (current_dividend / d10) ** (1 / 10) - 1
            ) * 100

    return result


def analyze_dividend_stability(annual):
    result = {
        "increase_count": 0,
        "decrease_count": 0,
        "flat_count": 0,
        "non_decrease_years": 0,
        "temporary_cut_candidate": False,
        "stability": "データ不足",
    }
    if annual is None or annual.empty:
        return result
    values = annual.sort_values("year")["dividend"].tolist()
    if len(values) < 2:
        return result

    increases, decreases, flats = 0, 0, 0
    for i in range(1, len(values)):
        prev, curr = safe_float(values[i - 1]), safe_float(values[i])
        if prev is None or curr is None:
            continue
        if curr > prev:
            increases += 1
        elif curr < prev:
            decreases += 1
        else:
            flats += 1

    result["increase_count"] = increases
    result["decrease_count"] = decreases
    result["flat_count"] = flats

    non_decrease = 0
    for i in range(len(values) - 1, 0, -1):
        prev, curr = safe_float(values[i - 1]), safe_float(values[i])
        if prev is None or curr is None:
            break
        if curr >= prev:
            non_decrease += 1
        else:
            break
    result["non_decrease_years"] = non_decrease

    if decreases == 0:
        result["stability"] = "非常に安定"
    elif decreases <= 1:
        result["stability"] = "比較的安定"
    else:
        result["stability"] = "減配履歴に注意"

    return result


def analyze_eps(info):
    eps = get_current_eps(info)
    if eps is None:
        return {
            "eps": None,
            "eps_status": "データ不足",
            "eps_message": "EPSデータを取得できませんでした。",
        }
    if eps > 0:
        return {
            "eps": eps,
            "eps_status": "OK",
            "eps_message": "会社は現在、1株あたりの利益を出しています。",
        }
    return {
        "eps": eps,
        "eps_status": "注意",
        "eps_message": (
            "EPSがマイナスです。利益面を慎重に確認してください。"
        ),
    }


def analyze_payout(payout, sector=None):
    if payout is None:
        return {
            "status": "データ不足",
            "message": "配当性向のデータを取得できませんでした。",
        }
    if payout < 30:
        status, message = (
            "余裕あり",
            "配当を維持・増やす余力を残している可能性があります。",
        )
    elif payout <= 50:
        status, message = (
            "適正目安",
            "一般的な高配当株の目安として確認しやすい水準です。",
        )
    elif payout <= 70:
        status, message = (
            "やや高い",
            "今後も利益が増えるか確認したい水準です。",
        )
    else:
        status, message = (
            "要注意",
            "利益に対する配当の割合が高めです。",
        )
    return {"status": status, "message": message}


def get_dividend_yield(info):
    dy = safe_float(info.get("dividendYield"))
    if dy is None:
        return None
    if dy <= 1:
        dy *= 100
    return dy


def overall_grade(
    dividend_yield,
    payout,
    eps,
    dividend_analysis,
    growth,
    market_cap,
):
    score = 0
    reasons, warnings = [], []

    if dividend_yield is not None:
        if dividend_yield >= 3:
            score += 2
            reasons.append("配当利回り3%以上")
        elif dividend_yield >= 2.5:
            score += 1
            reasons.append("配当利回り2.5%以上")
        else:
            warnings.append("配当利回りが2.5%未満")

    if eps is not None and eps > 0:
        score += 2
        reasons.append("EPSがプラス")
    else:
        score -= 2
        warnings.append("EPSがマイナスまたは不足")

    if payout is not None:
        if 30 <= payout <= 50:
            score += 2
            reasons.append("配当性向が30～50%")
        elif payout > 70:
            score -= 2
            warnings.append("配当性向が高い")

    if dividend_analysis["increase_count"] >= 7:
        score += 2
        reasons.append("増配回数7回以上")
    if dividend_analysis["decrease_count"] == 0:
        score += 2
        reasons.append("減配なし")

    if score >= 10:
        grade = "S"
    elif score >= 7:
        grade = "A"
    elif score >= 4:
        grade = "B"
    else:
        grade = "C"
    return grade, reasons, warnings


def diagnose_stock(code):
    data = get_stock_data(code)
    if not data or not data.get("info"):
        return None

    info = data["info"]
    hist = data["hist"]
    annual_dividend = get_dividend_history(code)
    dividend_analysis = analyze_dividend_stability(annual_dividend)
    growth = calculate_dividend_growth(annual_dividend)
    eps_analysis = analyze_eps(info)
    payout = get_current_payout(info)
    sector = info.get("sector")
    payout_analysis = analyze_payout(payout, sector)
    dividend_yield = get_dividend_yield(info)
    market_cap = safe_float(info.get("marketCap"))
    price = safe_float(info.get("currentPrice"))
    if price is None and not hist.empty:
        price = safe_float(hist["Close"].iloc[-1])

    grade, reasons, warnings = overall_grade(
        dividend_yield,
        payout,
        eps_analysis["eps"],
        dividend_analysis,
        growth,
        market_cap,
    )

    return {
        "code": code,
        "name": info.get("longName", info.get("shortName", code)),
        "sector": sector or "不明",
        "price": price,
        "yield": dividend_yield,
        "market_cap": market_cap,
        "eps": eps_analysis["eps"],
        "eps_status": eps_analysis["eps_status"],
        "eps_message": eps_analysis["eps_message"],
        "payout": payout,
        "payout_status": payout_analysis["status"],
        "payout_message": payout_analysis["message"],
        "dividend_increases": dividend_analysis["increase_count"],
        "dividend_decreases": dividend_analysis["decrease_count"],
        "non_decrease_years": dividend_analysis["non_decrease_years"],
        "temporary_cut": dividend_analysis["temporary_cut_candidate"],
        "stability": dividend_analysis["stability"],
        "dividend_5y_multiple": growth["dividend_5y_multiple"],
        "dividend_10y_multiple": growth["dividend_10y_multiple"],
        "dividend_5y_cagr": growth["dividend_5y_cagr"],
        "dividend_10y_cagr": growth["dividend_10y_cagr"],
        "grade": grade,
        "reasons": reasons,
        "warnings": warnings,
    }


def show_links(code):
    c1, c2 = st.columns(2)
    with c1:
        st.link_button("📊 Yahoo!ファイナンス", yahoo_url(code))
    with c2:
        st.link_button("📚 IR BANK", irbank_url(code))


def grade_box(grade):
    if grade == "S":
        st.success(
            "🟢 S判定：高配当株として重要な条件を多く満たしています。"
        )
    elif grade == "A":
        st.success(
            "🟢 A判定：全体的に良好ですが、いくつか確認したい点があります。"
        )
    elif grade == "B":
        st.warning(
            "🟡 B判定：良いところがありますが、注意点もあります。"
        )
    else:
        st.error(
            "🔴 C判定：配当を長く維持できるか慎重に確認したい銘柄です。"
        )


# =========================================================
# メインUI
# =========================================================

st.markdown(
    '<div class="main-title">📈 日本株・高配当AI秘書</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-title">EPS・配当性向・配当履歴・成長率から「長く配当をもらえる会社か」を確認します。</div>',
    unsafe_allow_html=True,
)

tabs = st.tabs(
    [
        "🏠 ダッシュボード",
        "🔍 個別診断",
        "📊 保有株診断",
        "🌐 高配当スクリーニング",
        "📚 累進配当確認",
        "📰 市場チェック",
    ]
)

with tabs[0]:
    st.header("🏠 高配当株AI秘書へようこそ")
    st.info(
        "このアプリは、配当利回りだけでなく『利益・配当性向・継続性・成長率』を総合的にチェックするツールです。"
    )

with tabs[1]:
    st.header("🔍 個別銘柄診断")
    code = st.text_input(
        "証券コードを入力", value="1928", max_chars=5
    ).strip().upper()
    if st.button("🔎 診断する", type="primary"):
        if not valid_code(code):
            st.error("正しい証券コードを入力してください（例: 1928, 353A）")
        else:
            with st.spinner("データを取得中..."):
                res = diagnose_stock(code)
            if not res:
                st.error("データを取得できませんでした。")
            else:
                st.subheader(f"{res['code']}：{res['name']}")
                show_links(code)
                grade_box(res["grade"])

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("株価", f"{fmt_money(res['price'])}円")
                c2.metric("配当利回り", fmt_pct(res["yield"]))
                c3.metric("EPS", f"{fmt_money(res['eps'])}円")
                c4.metric("配当性向", fmt_pct(res["payout"]))

                if res["reasons"]:
                    st.markdown("### 🟢 良いところ")
                    for r in res["reasons"]:
                        st.write(f"・{r}")
                if res["warnings"]:
                    st.markdown("### 🟡 注意点")
                    for w in res["warnings"]:
                        st.write(f"・{w}")

with tabs[2]:
    st.header("📊 保有株まとめ診断")
    if st.button("🚀 保有株を一括診断", type="primary"):
        rows = []
        progress = st.progress(0)
        total = len(MY_PORTFOLIO)
        for i, (c, name) in enumerate(MY_PORTFOLIO.items()):
            res = diagnose_stock(c)
            if res:
                rows.append(
                    {
                        "コード": c,
                        "銘柄名": name,
                        "業種": res["sector"],
                        "利回り": res["yield"],
                        "EPS": res["eps"],
                        "配当性向": res["payout"],
                        "増配回数": res["dividend_increases"],
                        "判定": res["grade"],
                    }
                )
            progress.progress((i + 1) / total)
        if rows:
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )

with tabs[3]:
    st.header("🌐 高配当株スクリーニング")
    uploaded_file = st.file_uploader(
        "銘柄一覧CSVをアップロード", type=["csv"]
    )
    if uploaded_file:
        try:
            df_u = pd.read_csv(uploaded_file, encoding="utf-8-sig")
        except:
            df_u = pd.read_csv(uploaded_file, encoding="cp932")
        st.success(f"{len(df_u):,}銘柄を読み込みました。")

with tabs[4]:
    st.header("📚 累進配当・株主還元方針確認")
    st.info(
        "公式サイトや中期経営計画の原文を確認するためのチェックリストです。"
    )
    for item in [
        "「累進配当」の記載があるか",
        "「減配しない」方針があるか",
        "最新決算説明資料を確認したか",
    ]:
        st.checkbox(item)

with tabs[5]:
    st.header("📰 市場チェック")
    st.write(
        "日経平均、ドル円、米国金利、保有株の決算や上方修正ニュースを確認しましょう。"
    )

st.divider()
st.caption(
    "※投資判断の補助ツールとしてご利用ください。データは取得時点のものです。"
)
