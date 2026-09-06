import streamlit as st
import yfinance as yf
import requests
import time
import pandas as pd

# ページ基本設定
st.set_page_config(page_title="高配当株 8ステップ分析ツール", layout="wide")

st.title("📈 高配当株 & 時価総額・財務分析ダッシュボード")
st.caption("東証33業種・全銘柄連携データ ｜ 個別全自動検索 & 最新中計・累進配当チェック & 配当トレンド分析")

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

# 主要な累進配当・還元方針データベース
PROGRESSIVE_DIVIDEND_STOCKS = {
    "9432": {"policy": "累進配当を継続実施中（中期経営計画にて明言）", "confidence": "高"},
    "9433": {"policy": "「KDDI VISION」等において持続的な増配・累進配当的な還元を志向", "confidence": "高"},
    "8593": {"policy": "「累進配当」を公式に採用・公言（三菱HCキャピタル）", "confidence": "高"},
    "8058": {"policy": "株主還元方針として継続的な配当維持・増配（実質的な累進姿勢）を表明", "confidence": "中"},
    "8031": {"policy": "三井物産：継続的な増配方針を掲げる", "confidence": "中"},
    "8001": {"policy": "伊藤忠商事：利益成長に伴う配当の継続的増加", "confidence": "中"},
    "2914": {"policy": "JT：株主還元方針として安定的な配当維持・成長を重視", "confidence": "中"},
    "8316": {"policy": "三井住友FG：累進的または積極的な還元方針", "confidence": "中"},
    "8306": {"policy": "三菱UFJフィナンシャル・グループ：安定・継続的な配当", "confidence": "中"}
}

tab1, tab2 = st.tabs(["🔍 個別銘柄を全自動検索・8ステップ診断", "📊 東証33業種・主要銘柄の一括比較"])

# ==========================================
# タブ1：個別銘柄の全自動検索・8ステップ詳細診断
# ==========================================
with tab1:
    st.subheader("個別銘柄 8ステップ詳細診断 ＆ 最新中計・原文チェック")
    st.write("証券コードを入力するか、一覧から銘柄を選択すると自動でデータ解析を行います。")
    
    stock_options = jpx_df.apply(lambda r: f"{r['コード']} - {r['銘柄名']} （{r['33業種区分']}）", axis=1).tolist()
    
    col_select, col_input = st.columns([2, 1])
    with col_select:
        selected_option = st.selectbox("銘柄リストから選択", stock_options, index=0)
        default_code = selected_option.split(" - ")[0]
    with col_input:
        ticker_code = st.text_input("直接コード入力（4桁）", value=default_code)

    target_code = ticker_code.strip() if ticker_code.strip() else default_code

    # ==========================================
    # ここに「みんかぶ」「IR BANK」へのリンクボタンを確実に配置
    # ==========================================
    st.markdown("---")
    st.markdown("##### 📌 【公式IR・中計・株主還元ページの確認】")
    link_col1, link_col2, _ = st.columns([1, 1, 2])
    minkabu_url = f"https://minkabu.jp/stock/{target_code}"
    irbank_url = f"https://irbank.net/{target_code}"
    link_col1.markdown(f"[🔗 みんかぶで詳細を見る]({minkabu_url})", unsafe_allow_html=True)
    link_col2.markdown(f"[🔗 IR BANKで中計・財務を見る]({irbank_url})", unsafe_allow_html=True)
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
                if raw_yield is not None:
                    if raw_yield > 1:
                        yield_pct = raw_yield / 100 if raw_yield > 20 else raw_yield
                    else:
                        yield_pct = raw_yield * 100
                else:
                    yield_pct = None

                payout_ratio = info.get("payoutRatio")
                payout_pct = payout_ratio * 100 if payout_ratio is not None else None
                per = info.get("trailingPE") or info.get("forwardPE")
                pbr = info.get("priceToBook")
                roe = info.get("returnOnEquity")
                roe_pct = roe * 100 if roe is not None else None
                market_cap = (info.get("marketCap") or 0) / 100000000
                profit_margins = info.get("profitMargins")
                profit_pct = profit_margins * 100 if profit_margins is not None else None
                equity_ratio = info.get("debtToEquity")

                st.success(f"### 【{jpx_name}】 （コード: {target_code} / 業種: {jpx_sector}）")
                
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("現在株価", f"¥{current_price:,.1f}" if current_price else "N/A")
                c2.metric("時価総額", f"{market_cap:,.0f} 億円" if market_cap > 0 else "N/A")
                c3.metric("配当利回り", f"{yield_pct:.2f} %" if yield_pct is not None else "N/A")
                c4.metric("PER", f"{per:.1f} 倍" if per else "N/A")
                c5.metric("PBR", f"{pbr:.2f} 倍" if pbr else "N/A")

                # 累進配当チェック
                st.markdown("---")
                st.write("### 🛡️ 累進配当・中期経営計画（中計）の公式記載チェック")
                if target_code in PROGRESSIVE_DIVIDEND_STOCKS:
                    policy_info = PROGRESSIVE_DIVIDEND_STOCKS[target_code]
                    st.success(f"🟢 **【累進配当方針の登録あり】**: {policy_info['policy']}")
                else:
                    st.info(f"⚪ **【要原文確認】**: この銘柄はシステム登録外です。上の「IR BANK」等を開き、**最新の中期経営計画PDFや株主還元ページ**に累進配当や減配なしの方針が書かれているか必ず原文をご確認ください。")

                st.markdown("---")
                st.write("### 📋 8ステップ詳細判定結果")

                steps = []
                if yield_pct is None:
                    steps.append(("1. 配当利回り", "⚪ データ取得不可", False))
                elif yield_pct >= 3.5:
                    steps.append(("1. 配当利回り", f"🟢 {yield_pct:.2f}% (合格: 3.5%以上)", True))
                elif yield_pct >= 2.5:
                    steps.append(("1. 配当利回り", f"🟡 {yield_pct:.2f}% (目安: 2.5%〜3.4%)", True))
                else:
                    steps.append(("1. 配当利回り", f"🔴 {yield_pct:.2f}% (基準未満: 2.5%未満)", False))

                if payout_pct is None:
                    steps.append(("2. 配当性向", "⚪ データ取得不可", False))
                elif payout_pct <= 50:
                    steps.append(("2. 配当性向", f"🟢 {payout_pct:.1f}% (健全: 50%以下)", True))
                elif payout_pct <= 70:
                    steps.append(("2. 配当性向", f"🟡 {payout_pct:.1f}% (やや高め: 50%〜70%)", True))
                else:
                    steps.append(("2. 配当性向", f"🔴 {payout_pct:.1f}% (過大: 70%超)", False))

                if market_cap <= 0:
                    steps.append(("3. 時価総額", "⚪ データ取得不可", False))
                elif market_cap >= 1000:
                    steps.append(("3. 時価総額", f"🟢 {market_cap:,.0f}億円 (大型株: 1000億円以上)", True))
                elif market_cap >= 300:
                    steps.append(("3. 時価総額", f"🟡 {market_cap:,.0f}億円 (中型株: 300億〜1000億円)", True))
                else:
                    steps.append(("3. 時価総額", f"🔴 {market_cap:,.0f}億円 (小型株: 300億円未満)", False))

                if per is None:
                    steps.append(("4. PER (割安度)", "⚪ データ取得不可", False))
                elif per <= 15:
                    steps.append(("4. PER (割安度)", f"🟢 {per:.1f}倍 (割安: 15倍以下)", True))
                else:
                    steps.append(("4. PER (割安度)", f"🔴 {per:.1f}倍 (割高傾向: 15倍超)", False))

                if pbr is None:
                    steps.append(("5. PBR (解散価値)", "⚪ データ取得不可", False))
                elif pbr <= 1.2:
                    steps.append(("5. PBR (解散価値)", f"🟢 {pbr:.2f}倍 (割安: 1.2倍以下)", True))
                else:
                    steps.append(("5. PBR (解散価値)", f"🔴 {pbr:.2f}倍 (割高傾向: 1.2倍超)", False))

                if roe_pct is None:
                    steps.append(("6. ROE (稼ぐ力)", "⚪ データ取得不可", False))
                elif roe_pct >= 8.0:
                    steps.append(("6. ROE (稼ぐ力)", f"🟢 {roe_pct:.1f}% (高効率: 8%以上)", True))
                else:
                    steps.append(("6. ROE (稼ぐ力)", f"🔴 {roe_pct:.1f}% (基準未満: 8%未満)", False))

                if profit_pct is None:
                    steps.append(("7. 営業利益率", "⚪ データ取得不可", False))
                elif profit_pct >= 10.0:
                    steps.append(("7. 営業利益率", f"🟢 {profit_pct:.1f}% (高収益: 10%以上)", True))
                else:
                    steps.append(("7. 営業利益率", f"🔴 {profit_pct:.1f}% (基準未満: 10%未満)", False))

                if equity_ratio is None:
                    steps.append(("8. 財務健全性", "⚪ データ取得不可", False))
                elif equity_ratio <= 100:
                    steps.append(("8. 財務健全性", f"🟢 D/Eレシオ {equity_ratio:.1f}% (健全: 100%以下)", True))
                else:
                    steps.append(("8. 財務健全性", f"🔴 D/Eレシオ {equity_ratio:.1f}% (負債やや多め)", False))

                passed_count = 0
                for title, desc, is_pass in steps:
                    if is_pass:
                        passed_count += 1
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

                try:
                    dividends = stock.dividends
                except Exception:
                    dividends = pd.Series()

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
                    
                    consec_inc = 0
                    for i in range(len(sorted_rec)):
                        if i == 0:
                            if sorted_rec[i]['type'] != "increase":
                                break
                            consec_inc += 1
                        else:
                            if sorted_rec[i]['type'] == "increase":
                                consec_inc += 1
                            else:
                                break

                    consec_non_dec = 0
                    for i in range(len(sorted_rec)):
                        if i == 0:
                            if sorted_rec[i]['type'] == "decrease":
                                break
                            consec_non_dec += 1
                        else:
                            if sorted_rec[i]['type'] in ["increase", "flat"]:
                                consec_non_dec += 1
                            else:
                                break

                    recent_10_recs = [r for r in sorted_rec if r['year'] >= sorted_rec[0]['year'] - 10]
                    inc_count_10 = sum(1 for r in recent_10_recs[1:] if r['type'] == "increase")
                    dec_count_10 = sum(1 for r in recent_10_recs[1:] if r['type'] == "decrease")

                    div_series = annual_div.set_index('FiscalYear')['Dividend']
                    latest_year = annual_div['FiscalYear'].max()

                    summary_rows = []
                    for period_name, years_back in [("5年増配率", 5), ("10年増配率", 10)]:
                        target_y = latest_year - years_back
                        if target_y in div_series.index and div_series[target_y] > 0:
                            start_val = div_series[target_y]
                            end_val = div_series[latest_year]
                            multiple = end_val / start_val
                            cagr = ((end_val / start_val) ** (1 / years_back) - 1) * 100
                            summary_rows.append({
                                "項目": period_name,
                                "増配率(倍)": f"{multiple:.1f}倍",
                                "平均増配率(%)": f"{cagr:.1f}%"
                            })
                        else:
                            summary_rows.append({
                                "項目": period_name,
                                "増配率(倍)": "データ不足",
                                "平均増配率(%)": "データ不足"
                            })

                    st.write("### 🏆 配当トレンド総合サマリー")
                    summary_box_data = [{
                        "銘柄名": jpx_name,
                        "連続増配年数": f"{consec_inc}年",
                        "連続非減配年数": f"{consec_non_dec}年",
                        "増配回数(10年)": f"{inc_count_10}回",
                        "減配回数(10年)": f"{dec_count_10}回",
                        "5年増配率": summary_rows[0]["増配率(倍)"],
                        "10年増配率": summary_rows[1]["増配率(倍)"],
                        "5年平均増配率": summary_rows[0]["平均増配率(%)"],
                        "10年平均増配率": summary_rows[1]["平均増配率(%)"]
                    }]
                    st.dataframe(pd.DataFrame(summary_box_data), use_container_width=True, hide_index=True)

                    st.write("### 📈 5年・10年 増配率（倍率＆平均）詳細")
                    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

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
                if raw_yield > 1:
                    yield_val = raw_yield / 100 if raw_yield > 20 else raw_yield
                else:
                    yield_val = raw_yield * 100
                
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
                    chart_data = df_result.set_index("銘柄名")["配当利回り(%)"]
                    st.bar_chart(chart_data)
                except Exception:
                    st.warning("グラフの生成をスキップしました。")
            else:
                st.dataframe(df_result, use_container_width=True, hide_index=True)
        else:
            st.warning("データの取得に失敗したか、対象データがありませんでした。時間を置いて再度お試しください。")
