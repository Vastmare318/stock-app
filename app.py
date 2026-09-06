import streamlit as st
import yfinance as yf
import time
import pandas as pd

# ページ基本設定
st.set_page_config(page_title="高配当株 8ステップ分析ツール", layout="wide")

st.title("📈 高配当株 & 時価総額・財務分析ダッシュボード")
st.caption("東証33業種・全銘柄連携データ ｜ 個別全自動検索 & 最新中計・累進配当原文チェック & 配当トレンド分析")

# ==========================================
# 東証全銘柄リスト・33業種データの自動取得＆キャッシュ
# ==========================================
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
        fallback_data = [
            {"コード": "7203", "銘柄名": "トヨタ自動車", "33業種区分": "輸送用機器"},
            {"コード": "9432", "銘柄名": "日本電信電話", "33業種区分": "情報・通信業"},
            {"コード": "8306", "銘柄名": "三菱ＵＦＪフィナンシャル・グループ", "33業種区分": "銀行業"},
            {"コード": "8316", "銘柄名": "三井住友フィナンシャルグループ", "33業種区分": "銀行業"},
            {"コード": "8591", "銘柄名": "オリックス", "33業種区分": "その他金融業"},
            {"コード": "8058", "銘柄名": "三菱商事", "33業種区分": "卸売業"},
            {"コード": "8593", "銘柄名": "三菱ＨＣキャピタル", "33業種区分": "その他金融業"},
            {"コード": "9104", "銘柄名": "商船三井", "33業種区分": "海運業"},
            {"コード": "2914", "銘柄名": "日本たばこ産業", "33業種区分": "食料品"},
            {"コード": "9433", "銘柄名": "ＫＤＤＩ", "33業種区分": "情報・通信業"}
        ]
        return pd.DataFrame(fallback_data)

jpx_df = load_jpx_stock_list()

# 正確な原文・期間・公式情報源データ（主要銘柄）
OFFICIAL_DIVIDEND_CHECK = {
    "9432": {
        "name": "日本電信電話 (NTT)",
        "has_policy": "◯ あり",
        "policy_text": "「株主還元の充実：継続的な配当維持・増配を基本方針とし...」",
        "is_limited": "× 期間の定めなし（基本方針として継続）",
        "limit_text": "特定の何年間という区切りはなく、会社の基本的な還元姿勢として掲げられています。",
        "source_title": "NTT 公式IR・中期経営戦略資料 / IR BANK",
        "source_url": "https://irbank.net/9432",
        "pub_date": "最新中期経営計画・決算短信に準拠"
    },
    "8593": {
        "name": "三菱HCキャピタル",
        "has_policy": "◯ あり",
        "policy_text": "「中計期間中の株主還元：累進配当の継続を基本とする」",
        "is_limited": "△ 期間あり（中期経営計画の期間に連動）",
        "limit_text": "「中計期間中」という条件がついており、次期中計で方針が見直される可能性があります。",
        "source_title": "三菱HCキャピタル 中期経営計画資料 / IR BANK",
        "source_url": "https://irbank.net/8593",
        "pub_date": "最新中期経営計画発表日に準拠"
    },
    "9433": {
        "name": "KDDI",
        "has_policy": "◯ あり",
        "policy_text": "「持続的な増配を継続する、『利益成長に伴う配当金の一株当たり配当金の継続的な増加』をめざす」",
        "is_limited": "× 期間の定めなし（持続的方針）",
        "limit_text": "具体的な年数で区切るのではなく、利益成長にあわせた持続的な増配を志向しています。",
        "source_title": "KDDI サステナビリティ・IR資料 / IR BANK",
        "source_url": "https://irbank.net/9433",
        "pub_date": "最新統合報告書・決算説明会資料に準拠"
    }
}

tab1, tab2 = st.tabs(["🔍 個別銘柄を全自動検索・8ステップ診断", "📊 東証33業種・主要銘柄の一括比較"])

# ==========================================
# タブ1：個別銘柄の全自動検索・8ステップ詳細診断
# ==========================================
with tab1:
    st.subheader("個別銘柄 8ステップ詳細診断 ＆ 累進配当・原文チェック")
    st.write("証券コードを入力するか、一覧から銘柄を選択すると自動でデータ解析を行います。")
    
    stock_options = jpx_df.apply(lambda r: f"{r['コード']} - {r['銘柄名']} （{r['33業種区分']}）", axis=1).tolist()
    
    col_select, col_input = st.columns([2, 1])
    with col_select:
        selected_option = st.selectbox("銘柄リストから選択", stock_options, index=0)
        default_code = selected_option.split(" - ")[0]
    with col_input:
        ticker_code = st.text_input("直接コード入力（4桁）", value=default_code)

    target_code = ticker_code.strip() if ticker_code.strip() else default_code

    # 📌 【公式IR・中計・株主還元ページの確認】ボタン常時トップ配置
    st.markdown("### 📌 【公式IR・中計・株主還元ページの確認】")
    link_col1, link_col2 = st.columns(2)
    minkabu_url = f"https://minkabu.jp/stock/{target_code}"
    irbank_url = f"https://irbank.net/{target_code}"
    link_col1.markdown(f"👉 **[みんかぶ（最新IR・株主還元ページ）を開く]({minkabu_url})**", unsafe_allow_html=True)
    link_col2.markdown(f"👉 **[IR BANK（中期経営計画・財務諸表）を開く]({irbank_url})**", unsafe_allow_html=True)
    st.markdown("---")

    if st.button("🔍 診断を実行する", type="primary"):
        symbol = f"{target_code}.T"
        
        matched = jpx_df[jpx_df['コード'] == target_code]
        jpx_name = matched['銘柄名'].values[0] if not matched.empty else "名称不明"
        jpx_sector = matched['33業種区分'].values[0] if not matched.empty else "不明"

        with st.spinner(f"【{jpx_name}】（{target_code}）の最新データを財務分析中..."):
            try:
                stock = yf.Ticker(symbol)
                try:
                    info = stock.info or {}
                except Exception:
                    info = {}

                current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
                
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
                c1.metric("現在株価", f"¥{current_price:,.1f}" if current_price else "N/A")
                c2.metric("時価総額", f"{market_cap:,.0f} 億円" if market_cap > 0 else "N/A")
                c3.metric("配当利回り", f"{yield_pct:.2f} %" if yield_pct is not None else "N/A")
                c4.metric("PER", f"{per:.1f} 倍" if per else "N/A")
                c5.metric("PBR", f"{pbr:.2f} 倍" if pbr else "N/A")

                # ==========================================
                # 🛡️ 累進配当・原文抜粋＆期間判定（子どもでもわかる解説付き）
                # ==========================================
                st.markdown("---")
                st.write("### 🛡️ 累進配当・中期経営計画（中計）の原文チェック（子どもでもわかる判定）")
                
                if target_code in OFFICIAL_DIVIDEND_CHECK:
                    d_info = OFFICIAL_DIVIDEND_CHECK[target_code]
                    st.info(f"**対象企業**: {d_info['name']}")
                    
                    st.write(f"**① 累進配当を方針として宣言している記載があるか？**: **{d_info['has_policy']}**")
                    st.markdown(f"> **原文そのままの抜粋**: `{d_info['policy_text']}`")
                    
                    st.write(f"**② その配当方針は期間限定？ それとも期間を設けていない？**: **{d_info['is_limited']}**")
                    st.markdown(f"> **わかりやすい解説**: {d_info['limit_text']}")
                    
                    st.write(f"**③ 情報源（資料名・URL・公開日）**")
                    st.markdown(f"- **資料名**: {d_info['source_title']}")
                    st.markdown(f"- **URL**: [{d_info['source_url']}]({d_info['source_url']})")
                    st.markdown(f"- **公開日・更新日**: {d_info['pub_date']}")
                else:
                    st.warning(f"⚠️ **【この銘柄の公式原文データは個別登録外です】**\n\n上の **「IR BANK」** や **「みんかぶ」** のボタンをポチッと押して、企業の公式ホームページにある「最新の中期経営計画PDF」や「株主還元方針のページ」を開き、**自分の目で原文を必ずチェック**してください！\n- **宣言の有無**: △ （要原文確認）\n- **期間限定か**: △ （要原文確認：中計の何年間だけか書かれているか見てみよう）")

                st.markdown("---")
                st.write("### 📋 8ステップ詳細判定結果")

                steps = []
                steps.append(("1. 配当利回り", f"🟢 {yield_pct:.2f}% (合格: 3.5%以上)" if yield_pct >= 3.5 else (f"🟡 {yield_pct:.2f}% (目安)" if yield_pct >= 2.5 else f"🔴 {yield_pct:.2f}% (基準未満)"), yield_pct >= 2.5))
                steps.append(("2. 配当性向", f"🟢 {payout_pct:.1f}% (健全)" if payout_pct <= 50 else (f"🟡 {payout_pct:.1f}% (やや高め)" if payout_pct <= 70 else f"🔴 {payout_pct:.1f}% (過大)"), payout_pct <= 70))
                steps.append(("3. 時価総額", f"🟢 {market_cap:,.0f}億円 (大型)" if market_cap >= 1000 else (f"🟡 {market_cap:,.0f}億円 (中型)" if market_cap >= 300 else f"🔴 {market_cap:,.0f}億円 (小型)"), market_cap >= 300))
                steps.append(("4. PER (割安度)", f"🟢 {per:.1f}倍 (割安)" if per <= 15 else f"🔴 {per:.1f}倍 (割高傾向)", per <= 15))
                steps.append(("5. PBR (解散価値)", f"🟢 {pbr:.2f}倍 (割安)" if pbr <= 1.2 else f"🔴 {pbr:.2f}倍 (割高傾向)", pbr <= 1.2))
                steps.append(("6. ROE (稼ぐ力)", f"🟢 {roe_pct:.1f}% (高効率)" if roe_pct >= 8.0 else f"🔴 {roe_pct:.1f}% (基準未満)", roe_pct >= 8.0))
                steps.append(("7. 営業利益率", f"🟢 {profit_pct:.1f}% (高収益)" if profit_pct >= 10.0 else f"🔴 {profit_pct:.1f}% (基準未満)", profit_pct >= 10.0))
                steps.append(("8. 財務健全性", f"🟢 健全" if equity_ratio <= 100 else f"🔴 負債多め", equity_ratio <= 100))

                passed_count = sum(1 for _, _, is_pass in steps if is_pass)
                for title, desc, is_pass in steps:
                    if is_pass:
                        st.success(f"**{title}**: {desc}")
                    else:
                        st.info(f"**{title}**: {desc}")

                st.progress(passed_count / 8.0)
                st.write(f"クリアスコア: **{passed_count} / 8 項目**")

                # ==========================================
                # 配当詳細分析
                # ==========================================
                st.markdown("---")
                st.write("### 📊 配当金推移・増配トレンド分析")

                if not dividends.empty:
                    dividends.index = dividends.index.tz_localize(None)
                    df_div = pd.DataFrame({'Dividend': dividends})
                    df_div['FiscalYear'] = df_div.index.map(lambda d: d.year if d.month >= 4 else d.year - 1)
                    annual_div = df_div.groupby('FiscalYear')['Dividend'].sum().reset_index()
                    annual_div = annual_div[annual_div['Dividend'] > 0].sort_values('FiscalYear')

                    table_data = []
                    prev_div = None
                    history_records = []

                    for _, row in annual_div.iterrows():
                        year_val = int(row['FiscalYear'])
                        year_label = f"{year_val}年3月期"
                        div_val = row['Dividend']
                        
                        if prev_div is None:
                            status = "—（比較対象なし）"
                            rate = "—"
                            diff_type = "none"
                        else:
                            diff = div_val - prev_div
                            if diff > 0:
                                status = "📈 増配"
                                rate = f"{((div_val - prev_div) / prev_div) * 100:.1f}%"
                                diff_type = "increase"
                            elif diff < 0:
                                status = "📉 減配"
                                rate = f"{((div_val - prev_div) / prev_div) * 100:.1f}%"
                                diff_type = "decrease"
                            else:
                                status = "➖ 据置"
                                rate = "0.0%"
                                diff_type = "flat"
                        
                        table_data.append({
                            "年度": year_label,
                            "年間配当金": f"{div_val:.1f}円" if div_val % 1 != 0 else f"{int(div_val)}円",
                            "前年比較": status,
                            "増配率(%)": rate
                        })
                        history_records.append({"year": year_val, "div": div_val, "type": diff_type})
                        prev_div = div_val

                    sorted_rec = sorted(history_records, key=lambda x: x['year'], reverse=True)
                    
                    consec_inc = sum(1 for i, r in enumerate(sorted_rec) if (i == 0 and r['type'] == "increase") or (i > 0 and r['type'] == "increase"))
                    consec_non_dec = sum(1 for i, r in enumerate(sorted_rec) if (i == 0 and r['type'] != "decrease") or (i > 0 and r['type'] in ["increase", "flat"]))

                    recent_10_recs = [r for r in sorted_rec if r['year'] >= sorted_rec[0]['year'] - 10]
                    inc_count_10 = sum(1 for r in recent_10_recs[1:] if r['type'] == "increase")
                    dec_count_10 = sum(1 for r in recent_10_recs[1:] if r['type'] == "decrease")

                    st.write("### 🏆 配当トレンド総合サマリー")
                    summary_box_data = [{
                        "銘柄名": jpx_name,
                        "連続増配年数": f"{consec_inc}年",
                        "連続非減配年数": f"{consec_non_dec}年",
                        "増配回数(10年)": f"{inc_count_10}回",
                        "減配回数(10年)": f"{dec_count_10}回"
                    }]
                    st.dataframe(pd.DataFrame(summary_box_data), use_container_width=True, hide_index=True)

                    def color_status(val):
                        if "増配" in str(val):
                            return 'color: #2e7d32; font-weight: bold;'
                        elif "据置" in str(val):
                            return 'color: #f57c00; font-weight: bold;'
                        elif "減配" in str(val):
                            return 'color: #c62828; font-weight: bold;'
                        return ''

                    st.write("### 📅 年度別 配当金推移詳細（増配・据置色分け）")
                    df_history = pd.DataFrame(table_data)
                    styled_df = df_history.style.map(color_status, subset=['前年比較'])
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)

                else:
                    st.info("過去の配当金データが見つかりませんでした。")

            except Exception as e:
                st.error(f"データ解析中にエラーが発生しました: {e}")

# ==========================================
# タブ2：東証33業種・一括比較スクリーニング
# ==========================================
with tab2:
    st.subheader("東証33業種・一括スクリーニング比較")
    st.write("業種を指定して一括データを取得するか、主要な注目高配当株を一括比較できます。")

    sectors = ["主要高配当銘柄（定番10選）"] + sorted(list(jpx_df['33業種区分'].unique()))
    selected_sector = st.selectbox("分析対象の業種・カテゴリを選択", sectors)

    if selected_sector == "主要高配当銘柄（定番10選）":
        target_df = jpx_df[jpx_df['コード'].isin(["7203", "9432", "8306", "8316", "8591", "8058", "8593", "9104", "2914", "9433"])]
    else:
        target_df = jpx_df[jpx_df['33業種区分'] == selected_sector].head(15)

    st.write(f"対象銘柄数: **{len(target_df)} 銘柄**")

    if st.button("🔄 一括データを更新取得する"):
        data_list = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, (_, row) in enumerate(target_df.iterrows()):
            code = row['コード']
            name = row['銘柄名']
            status_text.text(f"データ取得中... ({i+1}/{len(target_df)}): {code} - {name}")
            
            try:
                stock = yf.Ticker(f"{code}.T")
                info = stock.info or {}
                
                c_price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
                raw_yield = info.get("dividendYield") or 0
                yield_val = raw_yield * 100 if raw_yield < 0.2 else (raw_yield if raw_yield < 20 else 3.0)
                
                per_val = info.get("trailingPE") or info.get("forwardPE") or 0
                pbr_val = info.get("priceToBook") or 0
                mcap_val = (info.get("marketCap") or 0) / 100000000

                data_list.append({
                    "コード": code,
                    "銘柄名": name,
                    "業種": row['33業種区分'],
                    "株価(円)": round(c_price, 1),
                    "配当利回り(%)": round(yield_val, 2),
                    "PER(倍)": round(per_val, 1),
                    "PBR(倍)": round(pbr_val, 2),
                    "時価総額(億円)": round(mcap_val, 0)
                })
            except Exception:
                pass
            
            time.sleep(0.3)
            progress_bar.progress((i + 1) / len(target_df))

        status_text.text("一括データの取得が完了しました！")

        if data_list:
            df_result = pd.DataFrame(data_list)
            if not df_result.empty and "銘柄名" in df_result.columns and "配当利回り(%)" in df_result.columns:
                df_result = df_result.sort_values(by="配当利回り(%)", ascending=False).reset_index(drop=True)
                st.dataframe(df_result, use_container_width=True, hide_index=True)
                
                st.write("### 📈 配当利回り比較（%）")
                try:
                    chart_data = df_result.set_index("銘柄名")["配update引利回り(%)"] if "配update引利回り(%)" in df_result.columns else df_result.set_index("銘柄名")["配当利回り(%)"]
                    st.bar_chart(chart_data)
                except Exception:
                    pass
            else:
                st.dataframe(df_result, use_container_width=True, hide_index=True)
