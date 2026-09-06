import streamlit as st
import yfinance as yf
import requests
import time
import pandas as pd

# ページ基本設定
st.set_page_config(page_title="高配当株 8ステップ分析ツール", layout="wide")

st.title("📈 高配当株 & 時価総額・財務分析ダッシュボード")
st.caption("東証33業種・全銘柄連携データ ｜ 個別全自動検索 & 業種別・主要銘柄一括比較")

# 海外IP制限回避の設定
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
})

# ==========================================
# 東証全銘柄リスト・33業種データの自動取得＆キャッシュ
# ==========================================
@st.cache_data(ttl=86400)
def load_jpx_stock_list():
    """JPX公式データから東証上場全銘柄のコード・銘柄名・33業種区分を取得"""
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

tab1, tab2 = st.tabs(["🔍 個別銘柄を全自動検索・8ステップ診断", "📊 東証33業種・主要銘柄の一括比較"])

# ==========================================
# タブ1：個別銘柄の全自動検索・8ステップ詳細診断
# ==========================================
with tab1:
    st.subheader("個別銘柄 8ステップ詳細診断")
    st.write("証券コードを入力するか、一覧から銘柄を選択すると自動でデータ解析を行います。")
    
    stock_options = jpx_df.apply(lambda r: f"{r['コード']} - {r['銘柄名']} （{r['33業種区分']}）", axis=1).tolist()
    
    col_select, col_input = st.columns([2, 1])
    with col_select:
        selected_option = st.selectbox("銘柄リストから選択", stock_options, index=0)
        default_code = selected_option.split(" - ")[0]
    with col_input:
        ticker_code = st.text_input("直接コード入力（4桁）", value=default_code)

    target_code = ticker_code.strip() if ticker_code.strip() else default_code

    if st.button("🔍 診断を実行する", type="primary"):
        symbol = f"{target_code}.T"
        
        matched = jpx_df[jpx_df['コード'] == target_code]
        jpx_name = matched['銘柄名'].values[0] if not matched.empty else "名称不明"
        jpx_sector = matched['33業種区分'].values[0] if not matched.empty else "不明"

        with st.spinner(f"【{jpx_name}】（{target_code}）の最新データを財務分析中..."):
            try:
                stock = yf.Ticker(symbol, session=session)
                info = stock.info or {}

                current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
                yield_rate = info.get("dividendYield")
                yield_pct = yield_rate * 100 if yield_rate is not None else None
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

                st.markdown("---")
                st.write("### 📋 8ステップ詳細判定結果")

                steps = []
                
                # 1. 配当利回り
                if yield_pct is None:
                    steps.append(("1. 配当利回り", "⚪ データ取得不可", False))
                elif yield_pct >= 3.5:
                    steps.append(("1. 配当利回り", f"🟢 {yield_pct:.2f}% (合格: 3.5%以上)", True))
                elif yield_pct >= 2.5:
                    steps.append(("1. 配当利回り", f"🟡 {yield_pct:.2f}% (目安: 2.5%〜3.4%)", True))
                else:
                    steps.append(("1. 配当利回り", f"🔴 {yield_pct:.2f}% (基準未満: 2.5%未満)", False))

                # 2. 配当性向
                if payout_pct is None:
                    steps.append(("2. 配当性向", "⚪ データ取得不可", False))
                elif payout_pct <= 50:
                    steps.append(("2. 配当性向", f"🟢 {payout_pct:.1f}% (健全: 50%以下)", True))
                elif payout_pct <= 70:
                    steps.append(("2. 配当性向", f"🟡 {payout_pct:.1f}% (やや高め: 50%〜70%)", True))
                else:
                    steps.append(("2. 配当性向", f"🔴 {payout_pct:.1f}% (過大: 70%超)", False))

                # 3. 時価総額
                if market_cap <= 0:
                    steps.append(("3. 時価総額", "⚪ データ取得不可", False))
                elif market_cap >= 1000:
                    steps.append(("3. 時価総額", f"🟢 {market_cap:,.0f}億円 (大型株: 1000億円以上)", True))
                elif market_cap >= 300:
                    steps.append(("3. 時価総額", f"🟡 {market_cap:,.0f}億円 (中型株: 300億〜1000億円)", True))
                else:
                    steps.append(("3. 時価総額", f"🔴 {market_cap:,.0f}億円 (小型株: 300億円未満)", False))

                # 4. PER
                if per is None:
                    steps.append(("4. PER (割安度)", "⚪ データ取得不可", False))
                elif per <= 15:
                    steps.append(("4. PER (割安度)", f"🟢 {per:.1f}倍 (割安: 15倍以下)", True))
                else:
                    steps.append(("4. PER (割安度)", f"🔴 {per:.1f}倍 (割高傾向: 15倍超)", False))

                # 5. PBR
                if pbr is None:
                    steps.append(("5. PBR (解散価値)", "⚪ データ取得不可", False))
                elif pbr <= 1.2:
                    steps.append(("5. PBR (解散価値)", f"🟢 {pbr:.2f}倍 (割安: 1.2倍以下)", True))
                else:
                    steps.append(("5. PBR (解散価値)", f"🔴 {pbr:.2f}倍 (割高傾向: 1.2倍超)", False))

                # 6. ROE
                if roe_pct is None:
                    steps.append(("6. ROE (稼ぐ力)", "⚪ データ取得不可", False))
                elif roe_pct >= 8.0:
                    steps.append(("6. ROE (稼ぐ力)", f"🟢 {roe_pct:.1f}% (高効率: 8%以上)", True))
                else:
                    steps.append(("6. ROE (稼ぐ力)", f"🔴 {roe_pct:.1f}% (基準未満: 8%未満)", False))

                # 7. 営業利益率
                if profit_pct is None:
                    steps.append(("7. 営業利益率", "⚪ データ取得不可", False))
                elif profit_pct >= 10.0:
                    steps.append(("7. 営業利益率", f"🟢 {profit_pct:.1f}% (高収益: 10%以上)", True))
                else:
                    steps.append(("7. 営業利益率", f"🔴 {profit_pct:.1f}% (基準未満: 10%未満)", False))

                # 8. 財務健全性
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
                stock = yf.Ticker(f"{code}.T", session=session)
                info = stock.info or {}
                
                c_price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
                yield_val = (info.get("dividendYield") or 0) * 100
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
            
            time.sleep(0.2)
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
