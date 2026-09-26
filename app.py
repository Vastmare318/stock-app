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
st.caption("保有銘柄の確認・4000銘柄からの8項目スクリーニング・個別財務診断")

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
# データ取得関数
# =========================================================

@st.cache_data(ttl=1800)
def get_stock_data(code):
    code_clean = str(code).strip().replace(".T", "")
    ticker = yf.Ticker(f"{code_clean}.T")
    result = {
        "code": code_clean,
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
        result["eps"] = info.get("trailingEps") or info.get("epsTrailingTwelveMonths")
        
        payout = info.get("payoutRatio")
        if payout is not None:
            if payout < 1:
                payout *= 100
            result["payout"] = payout
            
        result["equity_ratio"] = info.get("debtToEquity")
    except Exception:
        pass

    # 配当性向の補完
    try:
        if result["dividend"] and result["eps"] and not result["payout"] and result["eps"] > 0:
            result["payout"] = (result["dividend"] / result["eps"]) * 100
    except Exception:
        pass

    return result

# =========================================================
# フォーマット関数
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
# ダッシュボードサマリー作成
# =========================================================

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
# タブメニュー
# =========================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "💰 保有銘柄一覧", 
    "🔎 4000銘柄・8項目スクリーニング検索", 
    "📊 個別銘柄・財務診断", 
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
# Tab 2: 4000銘柄・8項目スクリーニング検索（新機能）
# ---------------------------------------------------------
with tab2:
    st.subheader("🔎 全約4000銘柄から個別検索 & 8項目評価チェッカー")
    st.write("気になる日本の銘柄コード（例: `7203`（トヨタ）, `8306`（三菱UFJ）, `9432`（NTT）など4桁の数字）を入力してください。ご提示いただいた8つの基準に照らし合わせて自動評価します。")
    
    input_code = st.text_input("証券コードを入力（4桁）", value="7203", max_chars=4)
    
    if input_code:
        with st.spinner(f"コード {input_code} のデータを取得し、8項目で評価しています..."):
            s_data = get_stock_data(input_code)
            
        if s_data["price"] is None and s_data["market_cap"] is None:
            st.error(f"指定されたコード「{input_code}」のデータが見つかりませんでした。正しい4桁の証券コードを入力してください。")
        else:
            st.success(f"銘柄コード：{input_code} のデータを取得しました！")
            
            # 基本メトリクス表示
            mc1, mc2, mc3, mc4 = st.columns(4)
            with mc1:
                st.metric("株価", yen(s_data["price"]))
            with mc2:
                st.metric("時価総額", market_cap_str(s_data["market_cap"]))
            with mc3:
                st.metric("配当利回り", percent(s_data["yield"]))
            with mc4:
                st.metric("配当性向", percent(s_data["payout"]))
                
            st.markdown("### 📋 ご提示いただいた8つの評価項目に基づく判定結果")
            
            # 8項目の判定ロジック構築
            # 1. 業界・時価総額
            mc_val = s_data["market_cap"]
            if mc_val is not None:
                if mc_val >= 1_000_000_000_000:
                    eval_1 = "🟢 1兆円以上（かなり安全・大型株）"
                elif mc_val >= 300_000_000_000:
                    eval_1 = "🟢 3,000億〜1兆円（安定寄り・中大型）"
                elif mc_val >= 100_000_000_000:
                    eval_2 = "🟡 1,000億〜3,000億円（やや安定・中型）"
                    eval_1 = eval_2
                else:
                    eval_1 = "⚠️ 1,000億円未満（小型株・不安定なケースに注意）"
            else:
                eval_1 = "- (時価総額データ確認中)"
                
            # 2. 配当利回り
            y_val = s_data["yield"]
            if y_val is not None:
                eval_2 = "🟢 2.5%以上クリア" if y_val >= 2.5 else "⚠️ 2.5%未満（基準未満の可能性）"
            else:
                eval_2 = "- (利回りデータ確認中)"
                
            # 3 & 4. 連続増配・非減配
            eval_3 = "要IR確認（過去の連続増配年数をチェック）"
            eval_4 = "要IR確認（コロナ等の特殊要因による一時的減配か、その後の回復を確認）"
            
            # 5. 増減配実績 (増配7回・減配1回以下目安)
            eval_5 = "要IR/IR BANK確認（増配回数・減配回数）"
            
            # 6. 増配率 (10%以上目安)
            eval_6 = "要IR BANK確認（5年・10年平均増配率・倍率）"
            
            # 7. 累進配当
            eval_7 = "要公式IR・中期経営計画確認（累進配当方針の宣言有無）"
            
            # 8. EPS・配当性向・営業CF・自己資本比率
            p_val = s_data["payout"]
            if p_val is not None:
                if 30 <= p_val <= 50:
                    p_text = "配当性向30〜50%（健全水準）"
                elif p_val < 30:
                    p_text = "配当性向30%以下（余力あり）"
                else:
                    p_text = "配当性向50%超（やや高め・負担注意）"
            else:
                p_text = "配当性向データ確認中"
            eval_8 = f"EPS 10年右肩上がりか要確認 / {p_text} / 営業CF黒字・自己資本比率40%以上（銀行・商社・不動産は業界比較）"

            eval_df = pd.DataFrame({
                "スクリーニング・評価項目": [
                    "① 業界トップクラス / 時価総額",
                    "② 配当利回り",
                    "③ 連続増配年数",
                    "④ 連続非減配年数",
                    "⑤ 増減配実績",
                    "⑥ 増配率",
                    "⑦ 累進配当方針",
                    "⑧ EPS・配当性向・営業CF・自己資本比率"
                ],
                "判定・ステータス": [
                    eval_1,
                    eval_2,
                    eval_3,
                    eval_4,
                    eval_5,
                    eval_6,
                    eval_7,
                    eval_8
                ]
            })
            
            st.dataframe(eval_df, use_container_width=True, hide_index=True)
            
            st.markdown("#### 🔗 詳細な深掘りリンク")
            lk1, lk2 = st.columns(2)
            with lk1:
                st.link_button(f"📊 Yahoo!ファイナンス ({input_code}) を見る", yahoo_url(input_code), use_container_width=True)
            with lk2:
                st.link_button(f"📚 IR BANK ({input_code}) で財務・10年推移を見る", irbank_url(input_code), use_container_width=True)

# ---------------------------------------------------------
# Tab 3: 個別銘柄・財務診断
# ---------------------------------------------------------
with tab3:
    st.subheader("📊 保有銘柄の個別財務診断")
    selected_code = st.selectbox(
        "診断する保有銘柄を選択",
        list(PORTFOLIO.keys()),
        format_func=lambda x: f"{x}  {PORTFOLIO[x]['name']}"
    )
    
    if selected_code:
        data = get_stock_data(selected_code)
        name = PORTFOLIO[selected_code]["name"]
        st.markdown(f"### 🔍 {name} ({selected_code})")
        
        dc1, dc2, dc3, dc4 = st.columns(4)
        with dc1:
            st.metric("株価", yen(data["price"]))
        with dc2:
            st.metric("配当利回り", percent(data["yield"]))
        with dc3:
            st.metric("EPS", "-" if data["eps"] is None else f"{data['eps']:.2f}円")
        with dc4:
            st.metric("配当性向", percent(data["payout"]))
            
        st.link_button("📊 Yahoo!ファイナンス", yahoo_url(selected_code))
        st.link_button("📚 IR BANK", irbank_url(selected_code))

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
