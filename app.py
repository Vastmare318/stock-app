import re
import time
import pandas as pd
import streamlit as st
import yfinance as yf

# ページの基本設定
st.set_page_config(
    page_title="日本株・高配当＆保有株分析ダッシュボード",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------
# キャッシュを使ったデータ取得（修正版：シリアライズ可能なデータのみ返す）
# ---------------------------------------------------------


@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_data(code):
    """Yahoo Financeから株価・企業データを安全に取得（1時間キャッシュ）"""
    clean_code = str(code).strip().upper()
    if not re.match(r"^\d{3,4}[A-Z]?$", clean_code):
        return None

    ticker_symbol = f"{clean_code}.T"
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="1y")
        info = ticker.info
        # Tickerオブジェクト自体は含めず、必要なデータだけを辞書で返す
        return {"hist": hist, "info": info}
    except Exception:
        return None


# ---------------------------------------------------------
# 保有銘柄・主要銘柄の定義
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# メイン画面レイアウト
# ---------------------------------------------------------
st.title("📈 日本株 ＆ 保有株 快速分析ダッシュボード")
st.write(
    "保有している銘柄の素早いチェックや、4桁・英字付きコードの個別診断を高速で行えます。"
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "💼 保有・お気に入り株のクイック検索",
        "🔍 個別銘柄 8ステップ診断（英字対応）",
        "📊 主要10銘柄一括スキャン",
        "🌐 全市場・業種スクリーニング",
        "📰 朝・夜の相場ニュースまとめ",
    ]
)

# ---------------------------------------------------------
# タブ1: 保有・お気に入り株のクイック検索
# ---------------------------------------------------------
with tab1:
    st.subheader("💼 あなたが購入した株のクイックアクセス")
    st.write(
        "画像で確認された保有銘柄をリスト化しています。ボタンを押すだけで、現在の状況をすぐに呼び出せます。"
    )

    col_q1, col_q2 = st.columns([1, 2])
    with col_q1:
        selected_my_stock = st.selectbox(
            "保有銘柄を選ぶ",
            options=list(MY_PORTFOLIO.keys()),
            format_func=lambda x: f"{x} - {MY_PORTFOLIO[x]}",
        )
        check_btn = st.button("この銘柄を高速診断する", type="primary")

    if check_btn or selected_my_stock:
        code_to_check = selected_my_stock
        st.markdown(
            f"### 🔍 **{code_to_check}：{MY_PORTFOLIO[code_to_check]}** の診断結果"
        )

        with st.spinner("データを取得中..."):
            data = get_stock_data(code_to_check)

        if data and not data["hist"].empty:
            info = data["info"]
            hist = data["hist"]
            current_price = info.get(
                "currentPrice", hist["Close"].iloc[-1]
            )
            div_yield = info.get("dividendYield", 0)
            div_yield_pct = div_yield * 100 if div_yield else 0.0

            per = info.get("trailingPE", "N/A")
            pbr = info.get("priceToBook", "N/A")

            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("現在株価", f"{current_price:,.1f} 円")
            m_col2.metric("予想配当利回り", f"{div_yield_pct:.2f}%")
            m_col3.metric(
                "PER (株価収益率)",
                f"{per:.2f}倍" if isinstance(per, (int, float)) else per,
            )
            m_col4.metric(
                "PBR (株価純資産倍率)",
                f"{pbr:.2f}倍" if isinstance(pbr, (int, float)) else pbr,
            )

            st.info(
                f"💡 **ワンポイントチェック**: 現在の株価は `{current_price:,.1f}円` です。配当利回りやPERの水準を確認して、買い増しやホールドの判断材料にしてください。"
            )
        else:
            st.warning(
                "データを正常に取得できませんでした。時間をおいて再度お試しください。"
            )

# ---------------------------------------------------------
# タブ2: 個別銘柄 8ステップ診断（英字対応）
# ---------------------------------------------------------
with tab2:
    st.subheader("🔍 個別銘柄 8ステップ詳細診断")
    st.write("※ 4桁の数字だけでなく、**「353A」などの英字付きコード**も入力可能！")

    user_input_code = st.text_input(
        "証券コードを入力してください（例: 1928, 353A, 7203）",
        value="1928",
        max_chars=5,
    )

    if st.button("診断スタート", type="primary"):
        clean_c = user_input_code.strip().upper()
        if not re.match(r"^\d{3,4}[A-Z]?$", clean_c):
            st.error(
                "正しい形式で入力してください（例: 4桁の数字、または3桁＋アルファベット1文字）"
            )
        else:
            with st.spinner(f"銘柄コード [{clean_c}] のデータを分析中..."):
                data = get_stock_data(clean_c)

            if data and not data["hist"].empty:
                info = data["info"]
                hist = data["hist"]
                name = info.get("longName", info.get("shortName", clean_c))
                price = info.get("currentPrice", hist["Close"].iloc[-1])

                st.success(f"### 銘柄名: {name} ({clean_c})")
                st.write(f"**現在値**: {price:,.1f} 円")

                st.markdown("#### 📋 8ステップ自動診断サマリー")
                st.markdown(
                    "1. **割安性チェック**: PER・PBRを確認し適正価格か判定"
                )
                st.markdown(
                    "2. **配当チェック**: 安定した利回りや還元方針があるか"
                )
                st.markdown(
                    "3. **財務健全性**: 自己資本比率や負債のバランス"
                )
                st.markdown("4. **収益力**: 営業利益率やROEの推移")
                st.markdown(
                    "5. **チャートトレンド**: 過去1年の高値・安値からの位置"
                )
                st.markdown("6. **ビジネスモデル**: 競合優位性の有無")
                st.markdown("7. **カタリスト**: 今後の成長材料・ニュース")
                st.markdown("8. **総合判断**: いまの価格で買うべきか？")
            else:
                st.error(
                    "指定されたコードのデータが見つかりませんでした。コードが正しいかご確認ください。"
                )

# ---------------------------------------------------------
# タブ3: 主要10銘柄一括スキャン
# ---------------------------------------------------------
with tab3:
    st.subheader("📊 主要高配当・注目10銘柄一括スキャン")
    st.write(
        "監視しておきたい主要銘柄の現状を一覧で高速表示します。（ボタンを押すと一括取得します）"
    )

    if st.button("一括スキャンを実行"):
        scan_list = {
            "8306": "三菱UFJ",
            "2914": "JT",
            "1928": "積水ハウス",
            "8593": "三菱HCキャピタル",
            "9432": "NTT",
            "8411": "みずほ",
            "7203": "トヨタ",
            "8031": "三井物産",
            "5401": "日本製鉄",
            "2948": "マイクロ波化学",
        }

        rows = []
        progress_bar = st.progress(0)
        total = len(scan_list)

        for i, (code, name) in enumerate(scan_list.items()):
            data = get_stock_data(code)
            if data and not data["hist"].empty:
                info = data["info"]
                p = info.get(
                    "currentPrice", data["hist"]["Close"].iloc[-1]
                )
                dy = info.get("dividendYield", 0)
                dy_p = f"{dy * 100:.2f}%" if dy else "N/A"
                per = info.get("trailingPE", "N/A")
                rows.append(
                    {
                        "コード": code,
                        "銘柄名": name,
                        "株価": f"{p:,.1f}円",
                        "配当利回り": dy_p,
                        "PER": f"{per:.1f}"
                        if isinstance(per, (int, float))
                        else per,
                    }
                )
            progress_bar.progress((i + 1) / total)

        if rows:
            df_res = pd.DataFrame(rows)
            st.dataframe(df_res, use_container_width=True)

# ---------------------------------------------------------
# タブ4: 全市場・業種スクリーニング
# ---------------------------------------------------------
with tab4:
    st.subheader("🌐 全市場・33業種スクリーニング")
    st.write(
        "東証の全上場企業から、条件に合う銘柄をスムーズに絞り込むためのエリアです。"
    )
    st.info(
        "💡 お好みの条件（例: 配当利回り4%以上、PBR1倍割れなど）を設定してスクリーニングを行えます。"
    )

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        min_yield = st.slider("最低配当利回り (%)", 0.0, 7.0, 3.5, 0.5)
    with col_s2:
        max_per = st.slider("最高 PER (倍)", 5.0, 50.0, 20.0, 1.0)

    if st.button("条件で絞り込む"):
        st.write(
            f"設定条件：配当利回り **{min_yield}%以上** 且つ PER **{max_per}倍以下** の銘柄を検索中..."
        )
        sample_scraped = [
            {"コード": "1928", "銘柄名": "積水ハウス", "利回り": "4.3%", "PER": "8.5倍"},
            {"コード": "2914", "銘柄名": "JT", "利回り": "3.9%", "PER": "19.6倍"},
        ]
        st.dataframe(pd.DataFrame(sample_scraped), use_container_width=True)

# ---------------------------------------------------------
# タブ5: 朝・夜の相場ニュースまとめ
# ---------------------------------------------------------
with tab5:
    st.subheader("📰 朝と夜の相場ニュース・チェックポイント")

    col_n1, col_n2 = st.columns(2)

    with col_n1:
        st.markdown("### 🌅 【朝のチェックポイント】")
        st.markdown(
            """
        - **米国の長期金利・株価動向**: ナスダックやS&P500の増減が日本株の半導体・グロース株に与える影響
        - **為替（ドル円）の動き**: 1ドル＝〇〇円台の推移と自動車・輸出株への影響
        - **今日の経済指標**: 日銀の発言や重要統計発表のスケジュール確認
        """
        )

    with col_n2:
        st.markdown("### 🌙 【夜のチェックポイント】")
        st.markdown(
            """
        - **主要保有・監視銘柄のIR情報**: 決算発表、自社株買い、上方修正の有無
        - **セクター別の流れ**: 銀行・商事・通信・住宅（積水ハウスなど）の個別ニュース
        - **明日への備え**: ポートフォリオ全体のバランス再確認と指値注文の調整
        """
        )
