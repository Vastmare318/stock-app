import streamlit as st
import pandas as pd
from pathlib import Path
import json

BASE=Path(__file__).parent; DATA=BASE/'data'
st.set_page_config(page_title='高配当株AI秘書',page_icon='📈',layout='centered')
st.markdown('<style>.block-container{max-width:720px;padding:1rem .8rem 3rem}button{min-height:48px}</style>',unsafe_allow_html=True)

def read(name):
 p=DATA/name
 if not p.exists(): return pd.DataFrame()
 try:return pd.read_csv(p)
 except:return pd.DataFrame()
portfolio=read('portfolio.csv'); final20=read('final_20.csv')
meta={}; mp=DATA/'metadata.json'
if mp.exists():
 try:meta=json.loads(mp.read_text(encoding='utf-8'))
 except:pass
if 'page' not in st.session_state:st.session_state.page='home'
if 'code' not in st.session_state:st.session_state.code=None
def go(page,code=None):st.session_state.page=page;st.session_state.code=code;st.rerun()
def clean(x):return str(x).replace('.0','')
def detail():
 if st.button('← ホーム'):go('home')
 code=st.session_state.code; rows=pd.concat([final20,portfolio],ignore_index=True)
 if 'code' not in rows:return
 rows=rows[rows.code.astype(str).str.replace('.0','',regex=False)==code]
 if rows.empty:st.warning('データがありません');return
 r=rows.iloc[0]; st.title(f"📊 {r.get('name','')}");st.caption(f'コード {code}')
 a,b=st.columns(2);a.metric('株価',r.get('price','-'));b.metric('配当利回り',r.get('yield','-'));a.metric('年間配当/株',r.get('dividend','-'));b.metric('保有株数',r.get('shares','-'))
 st.subheader('判定'); cols=st.columns(2)
 fields=[('grade','判定'),('market_cap','時価総額'),('eps','EPS'),('payout_ratio','配当性向'),('increase_count','増配回数'),('cut_count','減配回数'),('non_decrease_years','非減配年数'),('dividend_cagr_5y','5年配当成長'),('dividend_cagr_10y','10年配当成長'),('eps_trend_10y','10年EPS'),('operating_cf','営業CF'),('equity_ratio','自己資本比率'),('progressive_dividend','累進配当')]
 for i,(k,l) in enumerate(fields):cols[i%2].write(f'**{l}**\n{r.get(k,"-")}')
 st.subheader('確認先');st.link_button('Yahoo Finance',f'https://finance.yahoo.co.jp/quote/{code}.T',use_container_width=True);st.link_button('Yahoo 配当履歴',f'https://finance.yahoo.co.jp/quote/{code}.T/dividend',use_container_width=True);st.link_button('IR BANK',f'https://irbank.net/{code}',use_container_width=True)
def home():
 st.title('📈 高配当株AI秘書');st.caption('高配当株をルールで絞り込み、保有株を管理')
 annual=0
 if not portfolio.empty and not final20.empty:
  m=portfolio.merge(final20,on='code',how='left',suffixes=('_p','_s'))
  if 'shares_p' in m and 'dividend' in m:annual=(pd.to_numeric(m.shares_p,errors='coerce').fillna(0)*pd.to_numeric(m.dividend,errors='coerce').fillna(0)).sum()
 a,b,c=st.columns(3);a.metric('保有',f'{len(portfolio)}銘柄');b.metric('年間予想配当',f'¥{annual:,.0f}');c.metric('候補',f'{len(final20)}銘柄')
 st.subheader('💰 保有株')
 for i in range(0,len(portfolio),2):
  cs=st.columns(2)
  for j in range(2):
   if i+j>=len(portfolio):break
   r=portfolio.iloc[i+j];code=clean(r.code)
   if cs[j].button(f"{r['name']}\n{int(r['shares'])}株",key=f'p{code}',use_container_width=True):go('detail',code)
 st.subheader('🔧 メニュー')
 if st.button('🔎 約4,000銘柄から20銘柄を探す',use_container_width=True):go('screening')
 if st.button('📊 個別診断',use_container_width=True):go('diagnosis')
 if st.button('📰 ニュース',use_container_width=True):go('news')
 if st.button('🔄 今すぐ更新',use_container_width=True):st.info('python update_screening.py を実行してください。')
 st.divider();st.caption(f"最終更新：{meta.get('last_screening_update','未実行')}");st.caption('次回更新：毎月1日を目安')
def screening():
 if st.button('← ホーム'):go('home')
 st.title('🔎 スクリーニング');st.caption(f"最終更新：{meta.get('last_screening_update','未実行')}")
 if final20.empty:st.warning('final_20.csv がありません。更新処理を実行してください。');return
 st.write(f'約3,897銘柄 → 条件抽出 → 深掘り → 最終{len(final20)}銘柄')
 for _,r in final20.iterrows():
  code=clean(r.code)
  if st.button(f"{r.get('grade','-')}　{r['name']}　利回り {r.get('yield','-')}",key=f's{code}',use_container_width=True):go('detail',code)
def diagnosis():
 if st.button('← ホーム'):go('home')
 st.title('📊 個別診断')
 if portfolio.empty:return
 choices=[f'{clean(r.code)} {r.name}' for _,r in portfolio.iterrows()];s=st.selectbox('銘柄',choices)
 if st.button('診断を見る',use_container_width=True):go('detail',s.split()[0])
def news():
 if st.button('← ホーム'):go('home')
 st.title('📰 ニュース');st.info('保有株ごとの最新ニュース取得機能を追加できる構成です。')
{'home':home,'screening':screening,'diagnosis':diagnosis,'news':news,'detail':detail}[st.session_state.page]()
