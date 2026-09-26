import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# =========================================================
# 基本設定
# =========================================================

st.set_page_config(
    page_title="高配当株AI秘書",
    page_icon="📈",
    layout="wide"
)

st.title("📈 高配当株AI秘書")
st.caption("保有銘柄の確認・4000銘柄からの配当履歴・増配率・累進配当の完全自動スクリーニング")

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
# データ取得・高度分析関数
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
        "consecutive_increases": 0,
        "consecutive_non_decrease": 0,
        "increase_count": 0,
        "decrease_count": 0,
        "annual_divs": pd.Series(dtype=float),
        "cagr": None,
        "has_progressive_policy": False,
        "long_business_summary": "",
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

    # 財務・指標・プロフィール情報
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
            
        # 企業概要テキストの取得（英語・日本語のキーワード検索用）
        summary = info.get("longBusinessSummary", "") or ""
        result["long_business_summary"] = summary
        
        # 累進配当や株主還元方針のキーワードチェック
        lower_summary = summary.lower()
        keywords = ["progressive", "doe", "dividend on equity", "stable dividend", "continuous increase", "shareholder return"]
        if any(kw in lower_summary for kw in keywords):
            result["has_progressive_policy"] = True
            
    except Exception:
        pass

    # 配当性向の補完
    try:
        if result["dividend"] and result["eps"] and not result["payout"] and result["eps"] > 0:
            result["payout"] = (result["dividend"] / result["eps"]) * 100
    except Exception:
        pass

    # 配当履歴の自動分析（連続増配・非減配・平均増配率CAGRの計算）
    try:
        divs = ticker.dividends
        if divs is not None and not divs.empty:
            annual = divs.groupby(divs.index.year).sum().sort_index()
            result["annual_divs"] = annual
            
            vals = annual.values.tolist()
            
            if len(vals) >= 2:
                # 連続増配年数
                inc_count = 0
                for i in range(len(vals) - 1, 0, -1):
                    if vals[i] > vals[i-1]:
                        inc_count += 1
                    else:
                        break
                
                # 非減配年数
                non_dec_count = 0
                for i in range(len(vals) - 1, 0, -1):
                    if vals[i] >= vals[i-1]:
                        non_dec_count += 1
                    else:
                        break
                        
                # 全期間の増減配カウント
                total_inc = 0
                total_dec = 0
                for i in range(1, len(vals)):
                    if vals[i] > vals[i-1]:
                        total_inc += 1
                    elif vals[i] < vals[i-1]:
                        total_dec += 1
                        
                result["consecutive_increases"] = inc_count
                result["consecutive_non_decrease"] = non_dec_count
                result["increase_count"] = total_inc
                result["decrease_count"] = total_dec
                
                # 平均増配率 (CAGR) の計算 (直近数年、最大5年間)
                valid_annual = annual[annual > 0]
                if len(valid_annual) >= 3:
                    start_val = valid_annual.iloc[-min(5, len(valid_annual))]
                    end_val = valid_annual.iloc[-1]
                    years_diff = len(valid_annual.tail(5)) - 1
                    if start_val > 0 and years_diff > 0:
                        cagr = ((end_val / start_val) ** (1 / years_diff) - 1) * 100
                        result["cagr"] = cagr
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
    "🔎 4000銘柄・完全自動スクリーニング", 
    "📊 個別銘柄・財務診断", 
    "📚 IR・企業情報"
])

# ---------------------------------------------------------
# Tab 1: 保有銘柄一覧
# ---------------------------------------------------------
with tab1:
    st.subheader("💰 保有銘柄一覧（10銘柄リスト）")
    st.write("保有している10銘柄の状況を一覧で確認できます。")
    
    display_df = pd.DataFrame({
        "コード": df_portfolio["code"],
        "銘柄名": df_portfolio["name"],
        "株価": df_portfolio["price"].apply(yen),
        "株数": df_portfolio["shares"].apply(lambda x: f"{int(x)}株"),
        "評価額": df_portfolio["value"].apply(yen),
        "利回り": df_portfolio["yield"].apply(percent),
        "年間配当": df_portfolio["annual_dividend"].apply(yen),
    })
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.markdown("#### 🔗 各銘柄の外部サイトリンク")
    for _, row in df_portfolio.iterrows():
        code = row["code"]
        name = row["name"]
        with st.expander(f"{code} : {name}"):
            b1, b2 = st.columns(2)
            with b1:
                st.link_button("📊 Yahoo!ファイナンスを見る", yahoo_url(code), use_container_width=True)
            with b2:
                st.link_button("📚 IR BANKを見る", irbank_url(code), use_container_width=True)

# ---------------------------------------------------------
# Tab 2: 4000銘柄・完全自動スクリーニング
# ---------------------------------------------------------
with tab2:
    st.subheader("🔎 全約4000銘柄から個別検索 & 8項目完全自動判定")
    st.write("調べたい銘柄の**4桁の証券コード**（例: 7012, 7203, 8306 等）を入力してください。すべての項目が自動判定されます。")
    
    input_code = st.text_input("証券コードを入力", value="7012", max_chars=4, key="screening_code_input")
    
    if input_code:
        with st.spinner(f"コード {input_code} の財務データおよび配当履歴を完全に解析中..."):
            s_data = get_stock_data(input_code)
            
        if s_data["price"] is None and s_data["market_cap"] is None:
            st.error(f"指定されたコード「{input_code}」のデータが見つかりませんでした。正しい4桁の証券コードを入力してください。")
        else:
            st.success(f"銘柄コード：{input_code} の自動判定が完了しました！")
            
            mc1, mc2, mc3, mc4 = st.columns(4)
            with mc1:
                st.metric("株価", yen(s_data["price"]))
            with mc2:
                st.metric("時価総額", market_cap_str(s_data["market_cap"]))
            with mc3:
                st.metric("配当利回り", percent(s_data["yield"]))
            with mc4:
                st.metric("配当性向", percent(s_data["payout"]))
                
            st.markdown("### 📋 8つの投資判断ルールに基づく自動判定結果")
            
            # 1. 時価総額
            mc_val = s_data["market_cap"]
            if mc_val is not None:
                if mc_val >= 1_000_000_000_000:
                    item1_stat = "🟢 合格（1兆円超・最高水準）"
                    item1_desc = "時価総額1兆円以上で非常に安全性が高い規模です。"
                elif mc_val >= 300_000_000_000:
                    item1_stat = "🟢 合格（3000億〜1兆円・安定）"
                    item1_desc = "長期投資の安心ライン（3000億円）をクリアしています。"
                elif mc_val >= 100_000_000_000:
                    item1_stat = "🟡 要注意（1000億〜3000億円）"
                    item1_desc = "中型株です。ボラティリティに注意してください。"
                else:
                    item1_stat = "🔴 基準外（1000億円未満）"
                    item1_desc = "小型株のため流動性や安定性に注意が必要です。"
            else:
                item1_stat = "- (確認中)"
                item1_desc = "時価総額データを取得できませんでした。"

            # 2. 配当利回り
            y_val = s_data["yield"]
            if y_val is not None:
                if y_val >= 2.5:
                    item2_stat = f"🟢 合格 ({y_val:.2f}%)"
                    item2_desc = "配当利回り2.5%の基準をクリアしています。"
                else:
                    item2_stat = f"🔴 基準外 ({y_val:.2f}%)"
                    item2_desc = "配当利回りが2.5%を下回っています。"
            else:
                item2_stat = "- (確認中)"
                item2_desc = "利回りデータを取得できませんでした。"

            # 3. 連続増配年数
            c_inc = s_data["consecutive_increases"]
            if c_inc >= 3:
                item3_stat = f"🟢 合格 ({c_inc}年連続増配)"
                item3_desc = f"過去の配当実績から直近 {c_inc} 年連続の増配を確認しました。"
            elif c_inc > 0:
                item3_stat = f"🟡 要注意 ({c_inc}年連続増配)"
                item3_desc = "連続増配年数が短めです。過去の推移を確認しましょう。"
            else:
                item3_stat = "🔴 基準外 (直近連続増配なし)"
                item3_desc = "直近の配当データで連続した増配を確認できませんでした。"

            # 4. 連続非減配年数
            c_non_dec = s_data["consecutive_non_decrease"]
            if c_non_dec >= 5:
                item4_stat = f"🟢 合格 ({c_non_dec}年以上減配なし)"
                item4_desc = f"直近 {c_non_dec} 年間は減配せずに安定しています。"
            else:
                item4_stat = f"🟡 要注意 (非減配期間: {c_non_dec}年)"
                item4_desc = "過去に減配実績があるか、データ期間が短いです。"

            # 5. 増減配実績
            inc_cnt = s_data["increase_count"]
            dec_cnt = s_data["decrease_count"]
            if dec_cnt <= 1:
                item5_stat = f"🟢 合格 (増配{inc_cnt}回 / 減配{dec_cnt}回)"
                item5_desc = "減配が1回以下に抑えられており優れた実績です。"
            else:
                item5_stat = f"🔴 要注意 (減配{dec_cnt}回あり)"
                item5_desc = f"過去に複数回（{dec_cnt}回）の減配実績があります。"

            # 6. 増配率（平均増配率 CAGR 自動計算）
            cagr_val = s_data["cagr"]
            annual_df = s_data["annual_divs"]
            history_str = " → ".join([f"{yr}: {val:.1f}円" for yr, val in list(annual_df.items())[-5:]]) if not annual_df.empty else "データなし"
            
            if cagr_val is not None:
                if cagr_val >= 10.0:
                    item6_stat = f"🟢 合格 (年率 +{cagr_val:.1f}%)"
                    item6_desc = f"直近の平均増配率が10%以上と非常に優秀です。\n(推移: {history_str})"
                elif cagr_val > 0:
                    item6_stat = f"🟡 要注意 (年率 +{cagr_val:.1f}%)"
                    item6_desc = f"増配はしていますが、年率10%の目安には届いていません。\n(推移: {history_str})"
                else:
                    item6_stat = f"🔴 基準外 (年率 {cagr_val:.1f}%)"
                    item6_desc = f"配当が成長傾向にありません。\n(推移: {history_str})"
            else:
                item6_stat = "ℹ️ データ確認中"
                item6_desc = f"配当履歴から増配率を算出できませんでした。\n(推移: {history_str})"

            # 7. 累進配当方針（キーワード自動判定）
            if s_data["has_progressive_policy"]:
                item7_stat = "🟢 合格 (累進配当・安定還元方針あり)"
                item7_desc = "企業の英文概要・方針テキストから「累進配当」「DOE」「安定配当」などのキーワードを検知しました。"
            else:
                item7_stat = "🟡 要確認 (キーワード未検知)"
                item7_desc = "自動検知では累進配当等の記述が見つかりませんでした。念のため公式IRをご確認ください。"

            # 8. 財務健全性
            p_val = s_data["payout"]
            if p_val is not None:
                if 30 <= p_val <= 50:
                    payout_judge = f"🟢 健全 ({p_val:.1f}%)"
                    payout_detail = "配当性向30〜50%の理想的な水準です。"
                elif p_val < 30:
                    payout_judge = f"🟢 余力あり ({p_val:.1f}%)"
                    payout_detail = "30%以下でさらなる増配の余力があります。"
                else:
                    payout_judge = f"🔴 高すぎ ({p_val:.1f}%)"
                    payout_detail = "配当性向が50%を超えており負担が高めです。"
            else:
                payout_judge = "- (確認中)"
                payout_detail = "配当性向データを取得中です。"

            item8_stat = payout_judge
            item8_desc = f"EPS実績 / {payout_detail} / 財務の安全性はIR BANKで最終チェック"

            eval_list = [
                ("① 業界トップクラス / 時価総額", item1_stat, item1_desc),
                ("② 配当利回り (目安: 2.5%以上)", item2_stat, item2_desc),
                ("③ 連続増配年数 (配当履歴から自動計算)", item3_stat, item3_desc),
                ("④ 連続非減配年数 (配当履歴から自動計算)", item4_stat, item4_desc),
                ("⑤ 増減配実績 (増減回数の自動集計)", item5_stat, item5_desc),
                ("⑥ 増配率 (目安: 年率10%以上・自動計算)", item6_stat, item6_desc),
                ("⑦ 累進配当方針 (企業方針キーワード自動検知)", item7_stat, item7_desc),
                ("⑧ 財務健全性 (配当性向・EPS)", item8_stat, item8_desc),
            ]

            for title, status, desc in eval_list:
                with st.container(border=True):
                    c_title, c_status = st.columns([3, 2])
                    with c_title:
                        st.markdown(f"**{title}**")
                        st.caption(desc)
                    with c_status:
                        st.markdown(f"### {status}")

            st.divider()
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
            st.link_button("📚 IR BANK", irbank_url(code), use_container_width=Thread if 'Thread' in globals() else irbank_url(code)) # 修正
        st.divider()

# =========================================================
# フッター
# =========================================================
st.caption("※株価・配当等のデータはYahoo Finance等から取得しています。実際の投資判断では最新の会社IRや中期経営計画等をご確認ください。")
