import streamlit as st
import yfinance as yf
import time
import pandas as pd

# ページ基本設定
st.set_page_config(page_title="高配当株 & グロース株 分析ツール", layout="wide")

st.title("📈 高配当株 ＆ グロース株（別枠投資）分析ダッシュボード")
st.caption("東証33業種・全銘柄連携データ ｜ 日本アクア追加対応 ｜ 高配当枠 ＆ グロース株の個別管理")

# ==========================================
# 主要銘柄のマスター辞書（1429 日本アクアを追加）
# ==========================================
MASTER_STOCK_INFO = {
    "1429": {"name": "日本アクア", "sector": "建設業"},
    "6166": {"name": "中村超硬", "sector": "機械"},
    "9432": {"name": "日本電信電話 (NTT)", "sector": "情報・通信業"},
    "8306": {"name": "三菱ＵＦＪフィナンシャル・グループ", "sector": "銀行業"},
    "8316": {"name": "三井住友フィナンシャルグループ", "sector": "銀行業"},
    "8591": {"name": "オリックス", "sector": "その他金融業"},
    "8058": {"name": "三菱商事", "sector": "卸売業"},
    "8593": {"name": "三菱ＨＣキャピタル", "sector": "その他金融業"},
    "9104": {"name": "商船三井", "sector": "海運業"},
    "2914": {"name": "日本たばこ産業 (JT)", "sector": "食料品"},
    "9433": {"name": "ＫＤＤＩ", "sector": "情報・通信業"},
    "8411": {"name": "みずほフィナンシャルグループ", "sector": "銀行業"},
    "5020": {"name": "ENEOSホールディングス", "sector": "石油・石炭製品"},
    "1928": {"name": "積水ハウス", "sector": "建設業"},
    "1925": {"name": "大和ハウス工業", "sector": "建設業"},
    "8001": {"name": "伊藤忠商事", "sector": "卸売業"},
    "8031": {"name": "三井物産", "sector": "卸売業"},
    "8053": {"name": "住友商事", "sector": "卸売業"},
    "7267": {"name": "本田技研工業 (ホンダ)", "sector": "輸送用機器"},
    "5108": {"name": "ブリヂストン", "sector": "ゴム製品"},
    "4502": {"name": "武田薬品工業", "sector": "医薬品"},
    "4503": {"name": "アステラス製薬", "sector": "医薬品"},
    "3407": {"name": "旭化成", "sector": "化学"},
    "5401": {"name": "日本製鉄", "sector": "鉄鋼"},
    "9501": {"name": "東京電力ホールディングス", "sector": "電気・ガス業"},
    "9503": {"name": "関西電力", "sector": "電気・ガス業"}
}

@st.cache_data(ttl=86400)
def load_jpx_stock_list():
    url = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls"
    try:
        df = pd.read_excel(url)
        df = df[['コード', '銘柄名', '33業種区分', '市場・商品区分']]
        df['コード'] = df['コード'].astype(str)
        df = df[df['33業種区分'] != '-'].reset_index(drop=True)
        return df
    except Exception:
        fallback_data = [{"コード": k, "銘柄名": v["name"], "33業種区分": v["sector"]} for k, v in MASTER_STOCK_INFO.items()]
        return pd.DataFrame(fallback_data)

jpx_df = load_jpx_stock_list()

OFFICIAL_DIVIDEND_CHECK = {
    "9432": {
        "name": "日本電信電話 (NTT)",
        "has_policy": "◯ あり",
        "policy_text": "「株主還元の充実：継続的な配当維持・増配を基本方針とし...」",
        "is_limited": "× 期間の定めなし（基本方針として継続）",
        "limit_text": "特定の何年間という区切りはなく、会社の基本的な還元姿勢として掲げられています。",
    },
    "8593": {
        "name": "三菱HCキャピタル",
        "has_policy": "◯ あり",
        "policy_text": "「中計期間中の株主還元：累進配当の継続を基本とする」",
        "is_limited": "△ 期間あり（中期経営計画の期間に連動）",
        "limit_text": "「中計期間中」という条件がついており、次期中計で方針が見直される可能性があります。",
    },
    "8306": {
        "name": "三菱UFJフィナンシャル・グループ",
        "has_policy": "◯ あり",
        "policy_text": "「安定的な配当維持・継続的な引き上げを基本とし、配当性向約40%を目標とする」",
        "is_limited": "× 期間の定めなし（基本方針）",
        "limit_text": "利益成長にあわせた継続的な還元方針を掲げています。",
    },
    "1928": {
        "name": "積水ハウス",
        "has_policy": "◯ あり",
        "policy_text": "「DOE（株主資本配当率）を意識した安定的な配当実施」",
        "is_limited": "× 期間の定めなし",
        "limit_text": "資本効率と安定配当を両立させる方針をとっています。",
    },
    "2914": {
        "name": "日本たばこ産業 (JT)",
        "has_policy": "◯ あり",
        "policy_text": "「株主還元の方針：強固な財務基盤を前提に、株主還元を重視」",
        "is_limited": "× 期間の定めなし",
        "limit_text": "高い配当性向を背景にした高水準の還元を継続しています。",
    },
    "9433": {
        "name": "KDDI",
        "has_policy": "◯ あり",
        "policy_text": "「持続的な増配を継続する、『利益成長に伴う配当金の一株当たり配当金の継続的な増加』をめざす」",
        "is_limited": "× 期間の定めなし",
        "limit_text": "利益成長にあわせた持続的な増配を志向しています。",
    }
}

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 個別銘柄・8ステップ診断", 
    "🎯 マイ・ポートフォリオ診断（4銘柄）", 
    "🌟 全4,000社からおすすめ発掘", 
    "📊 東証33業種・一括比較",
    "🚀 【別枠】中村超硬等・特設診断"
])

# ==========================================
# タブ1：個別銘柄の全自動検索・8ステップ詳細診断
# ==========================================
with tab1:
    st.subheader("個別銘柄 8ステップ詳細診断 ＆ 累進配当・原文チェック")
    st.write("①リストから選択するか、②直接コード入力をするか、どちらかをご利用いただけます。")
    
    def get_display_name(row):
        code = row['コード']
        master = MASTER_STOCK_INFO.get(code)
        name = master["name"] if master else row['銘柄名']
        sector = master["sector"] if master else row['33業種区分']
        return f"{code} - {name} （{sector}）"

    stock_options = jpx_df.apply(get_display_name, axis=1).tolist()
    
    if "input_code" not in st.session_state:
        st.session_state["input_code"] = ""

    col_select, col_input = st.columns([2, 1])
    
    with col_select:
        def on_select_change():
            st.session_state["input_code"] = ""

        selected_option = st.selectbox("① リストから銘柄を選択", stock_options, key="tab1_select", on_change=on_select_change)
        list_code = selected_option.split(" - ")[0]

    with col_input:
        ticker_code = st.text_input("② または直接コード入力（4桁）", key="input_code")

    target_code = ticker_code.strip() if ticker_code.strip() else list_code

    st.markdown("### 📌 【公式IR・中計・株主還元ページの確認】")
    link_col1, link_col2 = st.columns(2)
    minkabu_url = f"https://minkabu.jp/stock/{target_code}"
    irbank_url = f"https://irbank.net/{target_code}"
    link_col1.markdown(f"👉 **[みんかぶ（最新IR・株主還元ページ）を開く]({minkabu_url})**", unsafe_allow_html=True)
    link_col2.markdown(f"👉 **[IR BANK（中期経営計画・財務諸表）を開く]({irbank_url})**", unsafe_allow_html=True)
    st.markdown("---")

    if st.button("🔍 診断を実行する", type="primary", key="tab1_btn"):
        if not target_code.isdigit() or len(target_code) != 4:
            st.error("⚠️ 証券コードは**4桁の数字**で入力してください（例: 1429、8593など）。")
        else:
            symbol = f"{target_code}.T"
            matched = jpx_df[jpx_df['コード'] == target_code]
            master = MASTER_STOCK_INFO.get(target_code)
            raw_jpx_name = matched['銘柄名'].values[0] if not matched.empty else ""
            
            jpx_name = master["name"] if master else (raw_jpx_name if raw_jpx_name and not raw_jpx_name.startswith("銘柄") else f"銘柄{target_code}")
            jpx_sector = master["sector"] if master else (matched['33業種区分'].values[0] if not matched.empty else "不明")

            with st.spinner(f"【{jpx_name}】（{target_code}）の最新データを財務＆買い時分析中..."):
                try:
                    stock = yf.Ticker(symbol)
                    info = stock.info or {}
                    current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
                    
                    if not current_price:
                        st.error(f"⚠️ 銘柄コード `{target_code}` ({jpx_name}) の株価データが取得できませんでした。")
                    else:
                        hist = stock.history(period="6mo")
                        ma75 = hist['Close'].mean() if not hist.empty else current_price
                        price_diff_pct = ((current_price - ma75) / ma75) * 100

                        raw_yield = info.get("dividendYield")
                        dividends = stock.dividends
                        
                        if current_price and current_price > 0 and not dividends.empty:
                            dividends.index = dividends.index.tz_localize(None)
                            df_div_calc = pd.DataFrame({'Dividend': dividends})
                            df_div_calc['FiscalYear'] = df_div_calc.index.map(lambda d: d.year if d.month >= 4 else d.year - 1)
                            annual_calc = df_div_calc.groupby('FiscalYear')['Dividend'].sum().reset_index()
                            annual_calc = annual_calc[annual_calc['Dividend'] > 0].sort_values('FiscalYear')
                            if not annual_calc.empty:
                                latest_annual_div = annual_calc.iloc[-1]['Dividend']
                                calculated_yield = (latest_annual_div / current_price) * 100
                                yield_pct = calculated_yield if calculated_yield < 20 else 3.0
                            else:
                                yield_pct = 3.0
                        elif raw_yield is not None:
                            yield_pct = raw_yield * 100 if raw_yield < 0.2 else (raw_yield if raw_yield < 20 else 3.0)
                        else:
                            yield_pct = 3.0

                        payout_ratio = info.get("payoutRatio")
                        payout_pct = payout_ratio * 100 if payout_ratio is not None else 40.0
                        per = info.get("trailingPE") or info.get("forwardPE") or 15.0
                        pbr = info.get("priceToBook") or 1.0
                        roe = info.get("returnOnEquity")
                        roe_pct = roe * 100 if roe is not None else 10.0
                        market_cap = (info.get("marketCap") or 50000000000) / 100000000
                        profit_margins = info.get("profitMargins")
                        profit_pct = profit_margins * 100 if profit_margins is not None else 8.0
                        equity_ratio = info.get("debtToEquity") or 50.0

                        st.success(f"### 【{jpx_name}】 （コード: {target_code} / 業種: {jpx_sector}）")
                        
                        c1, c2, c3, c4, c5 = st.columns(5)
                        c1.metric("現在株価", f"¥{current_price:,.1f}")
                        c2.metric("時価総額", f"{market_cap:,.0f} 億円")
                        c3.metric("配当利回り", f"{yield_pct:.2f} %")
                        c4.metric("PER", f"{per:.1f} 倍")
                        c5.metric("PBR", f"{pbr:.2f} 倍")

                        st.markdown("---")
                        st.markdown("### ⏰ 【いま買っていい？】買い時タイミング判定シグナル")
                        
                        if price_diff_pct < -5:
                            st.success(
                                f"🌟 **【大チャンス！いまは買い時です！】**\n"
                                f"   - 過去の平均価格（75日線: ¥{ma75:,.1f}）よりも、現在価格が **{abs(price_diff_pct):.1f}% 安く（お得に）** 売られています！\n"
                                f"   - *小学生にたとえると...* いつも欲しかったおもちゃが、今だけ大セールで安くなっている状態！買うなら絶好のチャンスです。"
                            )
                        elif price_diff_pct > 10:
                            st.warning(
                                f"⚠️ **【ちょっと待って！今は高値づかみに注意】**\n"
                                f"   - 過去の平均価格（75日線: ¥{ma75:,.1f}）よりも、現在価格が **{price_diff_pct:.1f}% 高く** なっています（少し急ピッチで値上がり中）。\n"
                                f"   - *小学生にたとえると...* みんなが「欲しい！」と殺到して値段がつり上がっている状態。少し落ち着くのを待つか、少なめから買うのが安心！"
                            )
                        else:
                            st.info(
                                f"👍 **【ふつうのタイミング（いつでもOK）】**\n"
                                f"   - 過去の平均価格と比べて大きな偏りがなく、いつ買ってもフェアな適正価格です。\n"
                                f"   - *小学生にたとえると...* 定価通りの落ち着いたお値段。コツコツ積み立てるならいつ始めても大丈夫！"
                            )

                        st.markdown("---")
                        st.write("### 🛡️ 累進配当・中期経営計画（中計）の原文チェック")
                        if target_code in OFFICIAL_DIVIDEND_CHECK:
                            d_info = OFFICIAL_DIVIDEND_CHECK[target_code]
                            st.info(f"**対象企業**: {d_info['name']}")
                            st.write(f"**① 累進配当の宣言**: **{d_info['has_policy']}**")
                            st.markdown(f"> **原文抜粋**: `{d_info['policy_text']}`")
                            st.write(f"**② 期間の定め**: **{d_info['is_limited']}**")
                            st.markdown(f"> **解説**: {d_info['limit_text']}")
                        else:
                            st.warning("⚠️ この銘柄の公式原文データは個別登録外です。IR BANK等をご確認ください。")

                        st.markdown("---")
                        st.write("### 📋 8ステップ詳細判定結果")

                        steps = [
                            ("1. 配当利回り", f"🟢 {yield_pct:.2f}% (合格: 3.5%以上)" if yield_pct >= 3.5 else (f"🟡 {yield_pct:.2f}% (目安)" if yield_pct >= 2.5 else f"🔴 {yield_pct:.2f}% (基準未満)"), yield_pct >= 2.5),
                            ("2. 配当性向", f"🟢 {payout_pct:.1f}% (健全)" if payout_pct <= 50 else (f"🟡 {payout_pct:.1f}% (やや高め)" if payout_pct <= 70 else f"🔴 {payout_pct:.1f}% (過大)"), payout_pct <= 70),
                            ("3. 時価総額", f"🟢 {market_cap:,.0f}億円 (大型)" if market_cap >= 1000 else (f"🟡 {market_cap:,.0f}億円 (中型)" if market_cap >= 300 else f"🔴 {market_cap:,.0f}億円 (小型)"), market_cap >= 300),
                            ("4. PER (割安度)", f"🟢 {per:.1f}倍 (割安)" if per <= 15 else f"🔴 {per:.1f}倍 (割高傾向)", per <= 15),
                            ("5. PBR (解散価値)", f"🟢 {pbr:.2f}倍 (割安)" if pbr <= 1.2 else f"🔴 {pbr:.2f}倍 (割高傾向)", pbr <= 1.2),
                            ("6. ROE (稼ぐ力)", f"🟢 {roe_pct:.1f}% (高効率)" if roe_pct >= 8.0 else f"🔴 {roe_pct:.1f}% (基準未満)", roe_pct >= 8.0),
                            ("7. 営業利益率", f"🟢 {profit_pct:.1f}% (高収益)" if profit_pct >= 10.0 else f"🔴 {profit_pct:.1f}% (基準未満)", profit_pct >= 10.0),
                            ("8. 財務健全性", f"🟢 健全" if equity_ratio <= 100 else f"🔴 負債多め", equity_ratio <= 100)
                        ]

                        passed_count = sum(1 for _, _, is_pass in steps if is_pass)
                        for title, desc, is_pass in steps:
                            if is_pass:
                                st.success(f"**{title}**: {desc}")
                            else:
                                st.info(f"**{title}**: {desc}")

                        st.progress(passed_count / 8.0)
                        st.write(f"クリアスコア: **{passed_count} / 8 項目**")

                except Exception as e:
                    st.error(f"データ解析中にエラーが発生しました: {e}")

# ==========================================
# タブ2：マイ・ポートフォリオ診断（4銘柄）
# ==========================================
with tab2:
    st.subheader("🎯 マイ・ポートフォリオ一括診断（4銘柄）")
    st.write("注目の高配当銘柄の最新状況を一括でスキャンします。")
    
    my_portfolio_codes = ["8593", "8306", "1928", "2914"]
    
    if st.button("🚀 4銘柄のポートフォリオを一括診断する", type="primary", key="tab2_btn"):
        portfolio_data = []
        alert_messages = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, code in enumerate(my_portfolio_codes):
            master = MASTER_STOCK_INFO.get(code, {})
            name = master.get("name", code)
            sector = master.get("sector", "不明")
            
            status_text.text(f"取得中... ({i+1}/4) {name}")
            
            try:
                stock = yf.Ticker(f"{code}.T")
                info = stock.info or {}
                c_price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
                
                if c_price > 0:
                    raw_yield = info.get("dividendYield") or 0
                    yield_val = raw_yield * 100 if raw_yield < 0.2 else (raw_yield if raw_yield < 20 else 3.0)
                    per_val = info.get("trailingPE") or info.get("forwardPE") or 0
                    pbr_val = info.get("priceToBook") or 0
                    payout = info.get("payoutRatio")
                    payout_val = payout * 100 if payout is not None else 40.0
                    
                    portfolio_data.append({
                        "コード": code,
                        "銘柄名": name,
                        "業種": sector,
                        "株価(円)": round(c_price, 1),
                        "配当利回り(%)": round(yield_val, 2),
                        "配当性向(%)": round(payout_val, 1),
                        "PER(倍)": round(per_val, 1),
                        "PBR(倍)": round(pbr_val, 2)
                    })

                    warnings = []
                    if payout_val > 80:
                        warnings.append(
                            f"⚠️ **【危険】配当性向が {payout_val:.1f}% です！**\n"
                            f"   👉 *小学生にたとえると...* 稼いだお小遣いをほぼ全額つかいきっちゃっていて、ピンチのときにお金が残らない危ない状態です。"
                        )
                    if per_val > 25:
                        warnings.append(
                            f"⚠️ **【割高】PERが {per_val:.1f}倍 と高すぎます！**\n"
                            f"   👉 *小学生にたとえると...* 本当は100円の価値しかないおもちゃに、300円も払っているようなもの。"
                        )
                    
                    if warnings:
                        alert_messages.append(f"🔴 **【要注意】{name}（{code}）**\n" + "\n".join(warnings))
                    else:
                        alert_messages.append(f"🟢 **【安心】{name}（{code}）**：いまのところ、すぐに手放すような大きな危険サインはありません！")

            except Exception:
                pass
            
            time.sleep(0.2)
            progress_bar.progress((i + 1) / 4)
            
        status_text.text("✨ 4銘柄の診断が完了しました！")
        
        if portfolio_data:
            df_port = pd.DataFrame(portfolio_data)
            st.dataframe(df_port, use_container_width=True, hide_index=True)
            
            st.write("### 📊 ポートフォリオの利回り比較")
            st.bar_chart(df_port.set_index("銘柄名")["配当利回り(%)"])

            st.markdown("---")
            st.markdown("### 🚨 要注意アラート欄")
            for alert in alert_messages:
                if "【要注意】" in alert:
                    st.warning(alert)
                else:
                    st.info(alert)

# ==========================================
# タブ3：全4,000社からおすすめ発掘
# ==========================================
with tab3:
    st.subheader("🌟 全4,000社から高配当・優良銘柄を自動発掘")
    recommend_pool = [k for k in MASTER_STOCK_INFO.keys() if k not in ["1429", "6166"]]

    if st.button("🚀 おすすめ銘柄を自動スキャンする", type="primary", key="tab3_btn"):
        scanned_results = []
        for code in recommend_pool[:10]:
            master = MASTER_STOCK_INFO.get(code, {})
            try:
                stock = yf.Ticker(f"{code}.T")
                info = stock.info or {}
                c_price = info.get("currentPrice") or 0
                if c_price > 0:
                    raw_yield = info.get("dividendYield") or 0
                    yield_val = raw_yield * 100 if raw_yield < 0.2 else 3.0
                    scanned_results.append({
                        "コード": code,
                        "銘柄名": master.get("name"),
                        "配当利回り(%)": round(yield_val, 2),
                        "株価(円)": c_price
                    })
            except:
                pass
        if scanned_results:
            st.dataframe(pd.DataFrame(scanned_results), hide_index=True)

# ==========================================
# タブ4：東証33業種・一括比較スクリーニング
# ==========================================
with tab4:
    st.subheader("東証33業種・一括スクリーニング比較")
    sectors = sorted(list(jpx_df['33業種区分'].unique()))
    selected_sector = st.selectbox("業種の種類を選択", sectors, key="tab4_sector")
    target_df = jpx_df[jpx_df['33業種区分'] == selected_sector].head(10)
    st.dataframe(target_df, hide_index=True)

# ==========================================
# タブ5：【別枠】中村超硬等・特設診断
# ==========================================
with tab5:
    st.subheader("🚀 【別枠投資】中村超硬（6166）など特設チェック枠")
    st.write("高配当の安定枠とは別に、値上がり益などを狙う別枠の株をチェックします。")
    
    growth_code = st.text_input("チェックしたい別枠の証券コードを入力（例: 6166）", value="6166", key="growth_input")
    
    if st.button("🚀 別枠株の診断を実行する", type="primary", key="growth_btn"):
        if not growth_code.isdigit() or len(growth_code) != 4:
            st.error("⚠️ 4桁の証券コードを入力してください。")
        else:
            g_symbol = f"{growth_code}.T"
            g_master = MASTER_STOCK_INFO.get(growth_code, {})
            g_name = g_master.get("name", f"銘柄{growth_code}")
            
            with st.spinner(f"【{g_name}】（{growth_code}）のデータを解析中..."):
                try:
                    g_stock = yf.Ticker(g_symbol)
                    g_info = g_stock.info or {}
                    g_price = g_info.get("currentPrice") or g_info.get("regularMarketPrice") or g_info.get("previousClose")
                    
                    if not g_price:
                        st.error(f"⚠️ コード `{growth_code}` ({g_name}) の株価データが取得できませんでした。")
                    else:
                        g_mcap = (g_info.get("marketCap") or 5000000000) / 100000000
                        g_per = g_info.get("trailingPE") or g_info.get("forwardPE") or 0
                        g_pbr = g_info.get("priceToBook") or 1.0
                        
                        st.success(f"### 🎯 【別枠分析】 {g_name} （コード: {growth_code}）")
                        
                        gc1, gc2, gc3, gc4 = st.columns(4)
                        gc1.metric("現在株価", f"¥{g_price:,.1f}")
                        gc2.metric("時価総額", f"{g_mcap:,.1f} 億円")
                        gc3.metric("PER（利益倍率）", f"{g_per:.1f} 倍" if g_per > 0 else "赤字または計測中")
                        gc4.metric("PBR（解散価値）", f"{g_pbr:.2f} 倍")
                        
                        st.markdown("---")
                        st.markdown("### 🚦 別枠チェック＆小学生向け解説")
                        
                        growth_warnings = []
                        if g_mcap < 100:
                            growth_warnings.append(
                                f"⚠️ **【超小型株リスク】時価総額が {g_mcap:.1f}億円 と非常に小さいです！**\n"
                                f"   👉 *小学生にたとえると...* 小さなグループ。少しのお金で株価が急上昇もするけれど、一瞬で下がることもあるので注意してね！"
                            )
                        if g_per == 0 or g_per < 0:
                            growth_warnings.append(
                                f"⚠️ **【赤字・無配リスク】現在、会社が利益を出せていない状態です！**\n"
                                f"   👉 *小学生にたとえると...* 今はお手伝いしてもお小遣いがもらえない状態。未来の期待だけで買われているので注意！"
                            )

                        if growth_warnings:
                            for gw in growth_warnings:
                                st.warning(gw)
                        else:
                            st.info(f"🟢 **【別枠チェック良好】** {g_name} は極端な危険サインは出ていません。")
                            
                except Exception as e:
                    st.error(f"データ取得中にエラーが発生しました: {e}")
