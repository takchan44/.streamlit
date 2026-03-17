import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import google.generativeai as genai

st.set_page_config(page_title="코스피 주식 대시보드", page_icon="📈",
                   layout="wide", initial_sidebar_state="expanded")

@st.cache_data(ttl=3600, show_spinner=False)
def load_kospi_stocks():
    """로컬 JSON → pykrx → KRX API 순으로 시도"""
    # 방법 1: 로컬 JSON 파일 (가장 빠르고 안정적)
    try:
        import json, os
        json_path = os.path.join(os.path.dirname(__file__), "kospi_stocks.json")
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if len(data) > 100:
            return data
    except Exception:
        pass

    # 방법 2: pykrx
    try:
        from pykrx import stock
        for i in range(5):
            d = (datetime.today() - timedelta(days=i)).strftime("%Y%m%d")
            tickers = stock.get_market_ticker_list(d, market="KOSPI")
            if tickers:
                result = {}
                for code in tickers:
                    n = stock.get_market_ticker_name(code)
                    if n: result[n] = code + ".KS"
                if len(result) > 100: return result
    except Exception:
        pass

    # 방법 3: KRX 데이터포탈 API
    try:
        import urllib.request, json, urllib.parse
        url = "https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        params = urllib.parse.urlencode({
            "bld": "dbms/MDC/STAT/standard/MDCSTAT01901",
            "mktId": "STK", "share": "1", "csvxls_isNo": "false"
        }).encode()
        req = urllib.request.Request(url, data=params, method="POST",
            headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/x-www-form-urlencoded",
                     "Referer": "https://data.krx.co.kr"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        result = {}
        for row in data.get("OutBlock_1", []):
            name = row.get("ISU_ABBRV", "").strip()
            code = row.get("ISU_SRT_CD", "").strip()
            if name and code: result[name] = code + ".KS"
        if len(result) > 100: return result
    except Exception:
        pass

    return BUILTIN_KOSPI

@st.cache_data(ttl=86400, show_spinner=False)
def load_nasdaq_stocks():
    """나스닥 전종목 — nasdaq-trader.com 공개 파일에서 로딩"""
    try:
        url = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=5000&exchange=NASDAQ&download=true"
        import urllib.request, json
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        rows = data["data"]["rows"]
        return {row["name"]: row["symbol"] for row in rows if row.get("symbol") and row.get("name")}
    except Exception:
        pass
    # 폴백: 주요 나스닥 종목
    return BUILTIN_NASDAQ

BUILTIN_KOSPI = {
    "삼성전자":"005930.KS","SK하이닉스":"000660.KS","LG에너지솔루션":"373220.KS",
    "삼성바이오로직스":"207940.KS","현대차":"005380.KS","셀트리온":"068270.KS",
    "기아":"000270.KS","KB금융":"105560.KS","신한지주":"055550.KS","POSCO홀딩스":"005490.KS",
    "LG화학":"051910.KS","삼성SDI":"006400.KS","현대모비스":"012330.KS","카카오":"035720.KS",
    "NAVER":"035420.KS","하나금융지주":"086790.KS","우리금융지주":"316140.KS",
    "삼성물산":"028260.KS","LG전자":"066570.KS","SK이노베이션":"096770.KS",
    "SK텔레콤":"017670.KS","KT":"030200.KS","한국전력":"015760.KS",
    "두산에너빌리티":"034020.KS","삼성생명":"032830.KS","에코프로비엠":"247540.KS",
    "에코프로":"086520.KS","포스코퓨처엠":"003670.KS","한국조선해양":"009540.KS",
    "삼성중공업":"010140.KS","현대중공업":"329180.KS","HD현대":"267250.KS",
    "현대글로비스":"086280.KS","아모레퍼시픽":"090430.KS","LG생활건강":"051900.KS",
    "하이브":"352820.KS","크래프톤":"259960.KS","카카오뱅크":"323410.KS",
    "카카오페이":"377300.KS","대한항공":"003490.KS","현대건설":"000720.KS",
    "HMM":"011200.KS","강원랜드":"035250.KS","한미약품":"128940.KS",
    "유한양행":"000100.KS","삼성전기":"009150.KS","삼성SDS":"018260.KS",
    "SK바이오팜":"326030.KS","HLB":"028300.KS","기업은행":"024110.KS",
    "미래에셋증권":"006800.KS","한화에어로스페이스":"012450.KS","두산밥캣":"241560.KS",
    "고려아연":"010130.KS","농심":"004370.KS","오리온":"271560.KS",
    "CJ제일제당":"097950.KS","종근당":"185750.KS","대웅제약":"069620.KS",
    "롯데쇼핑":"023530.KS","이마트":"139480.KS","GS리테일":"007070.KS",
    "현대백화점":"069960.KS","한화솔루션":"009830.KS","CJ ENM":"035760.KS",
    "스튜디오드래곤":"253450.KS","엔씨소프트":"036570.KS","넷마블":"251270.KS",
    "GS건설":"006360.KS","DL이앤씨":"375500.KS","호텔신라":"008770.KS",
    "삼성증권":"016360.KS","NH투자증권":"005940.KS","SM엔터테인먼트":"041510.KS",
    "JYP엔터테인먼트":"035900.KS","LG":"003550.KS","SK":"034730.KS",
    "금호석유":"011780.KS","코웨이":"021240.KS",
}

BUILTIN_NASDAQ = {
    "Apple":"AAPL","Microsoft":"MSFT","NVIDIA":"NVDA","Amazon":"AMZN",
    "Meta Platforms":"META","Alphabet Class A":"GOOGL","Alphabet Class C":"GOOG",
    "Tesla":"TSLA","Broadcom":"AVGO","Netflix":"NFLX","AMD":"AMD",
    "Intel":"INTC","Qualcomm":"QCOM","Texas Instruments":"TXN",
    "Micron Technology":"MU","Applied Materials":"AMAT","ASML":"ASML",
    "Costco":"COST","PepsiCo":"PEP","Starbucks":"SBUX","Booking Holdings":"BKNG",
    "Lam Research":"LRCX","KLA Corporation":"KLAC","Analog Devices":"ADI",
    "Marvell Technology":"MRVL","Palo Alto Networks":"PANW","CrowdStrike":"CRWD",
    "Datadog":"DDOG","Snowflake":"SNOW","Palantir":"PLTR","Uber":"UBER",
    "Airbnb":"ABNB","Coinbase":"COIN","MercadoLibre":"MELI","Pinduoduo":"PDD",
    "JD.com":"JD","Baidu":"BIDU","NetEase":"NTES","Trip.com":"TCOM",
    "Moderna":"MRNA","Biogen":"BIIB","Gilead Sciences":"GILD","Illumina":"ILMN",
    "Intuitive Surgical":"ISRG","Align Technology":"ALGN","Regeneron":"REGN",
    "Vertex Pharmaceuticals":"VRTX","Amgen":"AMGN","Cintas":"CTAS",
    "Fastenal":"FAST","Old Dominion Freight":"ODFL","Workday":"WDAY",
    "Fortinet":"FTNT","Zscaler":"ZS","ServiceNow":"NOW","Splunk":"SPLK",
    "MongoDB":"MDB","HubSpot":"HUBS","Cloudflare":"NET","Okta":"OKTA",
}

# ── 세션 초기화 ─────────────────────────────────────────
if "portfolio"       not in st.session_state: st.session_state.portfolio = []
if "watchlist"       not in st.session_state: st.session_state.watchlist = ["005930.KS","000660.KS","035420.KS","AAPL","NVDA"]
if "selected_ticker" not in st.session_state: st.session_state.selected_ticker = "005930.KS"
if "kospi_loaded"    not in st.session_state: st.session_state.kospi_loaded = False
if "nasdaq_loaded"   not in st.session_state: st.session_state.nasdaq_loaded = False
if "chart_period"    not in st.session_state: st.session_state.chart_period = "일"
if "drawn_lines"     not in st.session_state: st.session_state.drawn_lines = []
if "market_tab"      not in st.session_state: st.session_state.market_tab = "코스피"
if "ma_settings"     not in st.session_state:
    st.session_state.ma_settings = [
        {"window":5,   "color":"#FF6B35","show":True},
        {"window":20,  "color":"#F5C518","show":True},
        {"window":60,  "color":"#C084FC","show":True},
        {"window":125, "color":"#FFFFFF","show":True},
    ]
if "vp_settings" not in st.session_state:
    st.session_state.vp_settings = {"bins":15,"color_above":"#3182F6","color_below":"#5BA3F5","show":True}
if "chart_height"    not in st.session_state: st.session_state.chart_height = 500
if "indicators"      not in st.session_state: st.session_state.indicators = []
if "auto_refresh"    not in st.session_state: st.session_state.auto_refresh = True
if "refresh_sec"     not in st.session_state: st.session_state.refresh_sec = 30
if "last_refresh"    not in st.session_state: st.session_state.last_refresh = 0

# ── 종목 로딩 ───────────────────────────────────────────
if not st.session_state.kospi_loaded:
    with st.spinner("코스피 전 종목 불러오는 중..."):
        KOSPI_STOCKS = load_kospi_stocks()
        st.session_state.kospi_stocks = KOSPI_STOCKS
        st.session_state.kospi_loaded = True
else:
    KOSPI_STOCKS = st.session_state.get("kospi_stocks", BUILTIN_KOSPI)

# 79개 이하면 재시도 (폴백 상태)
if len(KOSPI_STOCKS) <= 79:
    load_kospi_stocks.clear()
    KOSPI_STOCKS = load_kospi_stocks()
    st.session_state.kospi_stocks = KOSPI_STOCKS

if not st.session_state.nasdaq_loaded:
    with st.spinner("나스닥 전 종목 불러오는 중..."):
        NASDAQ_STOCKS = load_nasdaq_stocks()
        st.session_state.nasdaq_stocks = NASDAQ_STOCKS
        st.session_state.nasdaq_loaded = True
else:
    NASDAQ_STOCKS = st.session_state.get("nasdaq_stocks", BUILTIN_NASDAQ)

# 전체 종목 통합 맵 (이름→티커, 티커→이름)
ALL_STOCKS = {**KOSPI_STOCKS, **NASDAQ_STOCKS}
TICKER_NAME_MAP = {v: k for k, v in ALL_STOCKS.items()}

def format_price(p):
    if not p: return "N/A"
    return f"₩{int(p):,}"

def format_cap(v):
    if not v: return "N/A"
    if v >= 1e12: return f"{v/1e12:.1f}조"
    elif v >= 1e8: return f"{v/1e8:.0f}억"
    return f"{v/1e9:.1f}B"

def hex_to_rgba(h, a):
    r,g,b = int(h[1:3],16),int(h[3:5],16),int(h[5:7],16)
    return f"rgba({r},{g},{b},{a})"

# ── Yahoo Finance 직접 호출 (yfinance 라이브러리 없이) ──
import urllib.request, json as _json, time as _time

_YF_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://finance.yahoo.com",
}

def _yf_get(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers=_YF_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return _json.loads(r.read().decode("utf-8"))
    except Exception:
        return None

@st.cache_data(ttl=30, show_spinner=False)
def get_stock_info(ticker):
    name_fallback = ticker.replace(".KS","").replace(".KQ","")

    # ── 방법1: v7 quote API (가장 정확 — 장중/장후 모두)
    url2 = f"https://query2.finance.yahoo.com/v7/finance/quote?symbols={ticker}"
    data2 = _yf_get(url2)
    if data2:
        try:
            q = data2["quoteResponse"]["result"][0]
            price = q.get("regularMarketPrice", 0)
            if price:
                chg     = q.get("regularMarketChange", 0) or 0
                chg_pct = q.get("regularMarketChangePercent", 0) or 0
                prev    = q.get("regularMarketPreviousClose", 0)
                # 등락률이 0이고 전일 종가가 있으면 직접 계산
                if chg_pct == 0 and prev and price != prev:
                    chg     = price - prev
                    chg_pct = (chg / prev * 100) if prev else 0
                return {
                    "currentPrice": price,
                    "regularMarketPrice": price,
                    "regularMarketChange": chg,
                    "regularMarketChangePercent": chg_pct,
                    "regularMarketVolume": q.get("regularMarketVolume", 0),
                    "fiftyTwoWeekHigh": q.get("fiftyTwoWeekHigh", 0),
                    "fiftyTwoWeekLow":  q.get("fiftyTwoWeekLow",  0),
                    "marketCap":  q.get("marketCap",  0),
                    "trailingPE": q.get("trailingPE", 0),
                    "longName":  q.get("longName") or q.get("shortName") or name_fallback,
                    "shortName": q.get("shortName") or name_fallback,
                }
        except Exception:
            pass

    # ── 방법2: v8 chart range=5d (최근 종가 2개로 등락 계산)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d"
    data = _yf_get(url)
    if data:
        try:
            result  = data["chart"]["result"][0]
            meta    = result["meta"]
            closes  = [c for c in (result["indicators"]["quote"][0].get("close") or []) if c]
            volumes = [v for v in (result["indicators"]["quote"][0].get("volume") or []) if v]
            price   = meta.get("regularMarketPrice") or (closes[-1] if closes else 0)
            prev    = meta.get("previousClose") or (closes[-2] if len(closes) >= 2 else price)
            chg     = price - prev if prev else 0
            chg_pct = (chg / prev * 100) if prev else 0
            name    = meta.get("shortName") or meta.get("longName") or name_fallback
            if price:
                return {
                    "currentPrice": price,
                    "regularMarketPrice": price,
                    "regularMarketChange": chg,
                    "regularMarketChangePercent": chg_pct,
                    "regularMarketVolume": volumes[-1] if volumes else meta.get("regularMarketVolume", 0),
                    "fiftyTwoWeekHigh": meta.get("fiftyTwoWeekHigh", 0),
                    "fiftyTwoWeekLow":  meta.get("fiftyTwoWeekLow",  0),
                    "marketCap":  meta.get("marketCap",  0),
                    "trailingPE": meta.get("trailingPE", 0),
                    "longName":  name,
                    "shortName": name,
                }
        except Exception:
            pass

    return None

@st.cache_data(ttl=300, show_spinner=False)
def get_history(ticker, period):
    period_map = {"5d":"5d","1mo":"1mo","3mo":"3mo","6mo":"6mo","1y":"1y","5y":"5y","10y":"10y"}
    interval_map = {"5d":"1d","1mo":"1d","3mo":"1d","6mo":"1d","1y":"1d","5y":"1wk","10y":"1mo"}
    p = period_map.get(period, "3mo")
    iv = interval_map.get(period, "1d")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval={iv}&range={p}"
    data = _yf_get(url)
    if data:
        try:
            res    = data["chart"]["result"][0]
            ts     = res["timestamp"]
            ohlcv  = res["indicators"]["quote"][0]
            opens  = ohlcv.get("open", [])
            highs  = ohlcv.get("high", [])
            lows   = ohlcv.get("low", [])
            closes = ohlcv.get("close", [])
            vols   = ohlcv.get("volume", [])
            idx = pd.to_datetime(ts, unit="s", utc=True).tz_convert("Asia/Seoul")
            df = pd.DataFrame({
                "Open":   opens,
                "High":   highs,
                "Low":    lows,
                "Close":  closes,
                "Volume": vols,
            }, index=idx)
            df = df.dropna(subset=["Close"])
            return df
        except Exception:
            pass
    return pd.DataFrame()

@st.cache_data(ttl=600, show_spinner=False)
def get_news(ticker):
    # Yahoo Finance 뉴스 API
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={ticker}&newsCount=5&quotesCount=0"
    data = _yf_get(url)
    if data:
        try:
            return data.get("news", [])[:5]
        except Exception:
            pass
    return []

# ── 사이드바 ────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 종목 검색")
    # 종목 수 표시 + 새로고침
    sc1, sc2 = st.columns([3,1])
    with sc1:
        kospi_cnt  = len(KOSPI_STOCKS)
        nasdaq_cnt = len(NASDAQ_STOCKS)
        status = "✅" if kospi_cnt > 100 else "⚠️"
        st.caption(f"{status} 코스피 {kospi_cnt:,}개 · 나스닥 {nasdaq_cnt:,}개")
    with sc2:
        if st.button("🔄", key="reload_stocks", help="종목 목록 새로고침"):
            load_kospi_stocks.clear()
            load_nasdaq_stocks.clear()
            st.session_state.kospi_loaded  = False
            st.session_state.nasdaq_loaded = False
            st.rerun()

    # 통합 검색창
    sq = st.text_input("종목명 또는 코드 검색", placeholder="삼성, AAPL, 005930, NVDA...")

    if sq:
        q = sq.strip().upper()
        # 코스피 + 나스닥 통합 검색
        kospi_res  = {n:t for n,t in KOSPI_STOCKS.items()  if q in n.upper() or q in t.replace(".KS","").upper()}
        nasdaq_res = {n:t for n,t in NASDAQ_STOCKS.items() if q in n.upper() or q in t.upper()}
        all_res = {**kospi_res, **nasdaq_res}

        if all_res:
            st.caption(f"코스피 {len(kospi_res)}개 · 나스닥 {len(nasdaq_res)}개")
            sel = st.selectbox(f"검색 결과 {len(all_res)}개", list(all_res.keys()),
                               format_func=lambda x: f"{'🇰🇷' if all_res[x].endswith('.KS') else '🇺🇸'} {x}  ({all_res[x].replace('.KS','')})")
            if st.button("조회", use_container_width=True, key="btn_search"):
                st.session_state.selected_ticker = all_res[sel]; st.rerun()
        else:
            st.caption("검색 결과가 없습니다.")
            if st.button(f"'{sq}' 직접 조회", use_container_width=True, key="btn_direct"):
                st.session_state.selected_ticker = sq.upper(); st.rerun()
    else:
        # 시장 탭 선택
        mkt = st.radio("시장", ["🇰🇷 코스피", "🇺🇸 나스닥"], horizontal=True, key="mkt_radio")
        is_kospi = "코스피" in mkt

        if is_kospi:
            stock_list = KOSPI_STOCKS
            st.caption(f"총 {len(stock_list):,}개 종목")
            names = list(stock_list.keys())
            cur   = TICKER_NAME_MAP.get(st.session_state.selected_ticker, names[0])
            didx  = names.index(cur) if cur in names else 0
            sel   = st.selectbox("종목 선택", names, index=didx,
                                 format_func=lambda x: f"{x}  ({stock_list[x].replace('.KS','')})")
            if st.button("조회", use_container_width=True, key="btn_kospi"):
                st.session_state.selected_ticker = stock_list[sel]; st.rerun()
        else:
            stock_list = NASDAQ_STOCKS
            st.caption(f"총 {len(stock_list):,}개 종목")
            names = list(stock_list.keys())
            cur   = TICKER_NAME_MAP.get(st.session_state.selected_ticker, names[0])
            didx  = names.index(cur) if cur in names else 0
            sel   = st.selectbox("종목 선택", names, index=didx,
                                 format_func=lambda x: f"{x}  ({stock_list[x]})")
            if st.button("조회", use_container_width=True, key="btn_nasdaq"):
                st.session_state.selected_ticker = stock_list[sel]; st.rerun()

    st.markdown("---")
    st.markdown("### ⭐ 관심 종목")
    to_remove = None
    for wt in st.session_state.watchlist:
        wi = get_stock_info(wt)
        wname = TICKER_NAME_MAP.get(wt, wt.replace(".KS",""))
        flag  = "🇰🇷" if wt.endswith(".KS") else "🇺🇸"
        c1,c2 = st.columns([5,1])
        if wi:
            wp = wi.get("currentPrice") or wi.get("regularMarketPrice",0)
            wc = wi.get("regularMarketChangePercent",0)
            color = "#22c55e" if wc>=0 else "#ef4444"
            sign  = "▲" if wc>=0 else "▼"
            price_str = f"₩{int(wp):,}" if wt.endswith(".KS") else f"${wp:,.2f}"
            with c1: st.markdown(f"""<div style="padding:4px 0;cursor:pointer;">
<span style="font-size:10px;color:#64748b;">{flag} {wt.replace('.KS','').replace('.KQ','')}</span><br>
<span style="font-size:12px;font-weight:600;color:#e2e8f0;">{wname}</span><br>
<span style="font-size:11px;font-family:monospace;color:#94a3b8;">{price_str}</span>
<span style="font-size:10px;color:{color};margin-left:4px;">{sign}{abs(wc):.2f}%</span>
</div>""", unsafe_allow_html=True)
        else:
            with c1: st.markdown(f"""<div style="padding:4px 0;">
<span style="font-size:10px;color:#64748b;">{flag} {wt.replace('.KS','')}</span><br>
<span style="font-size:12px;font-weight:600;color:#e2e8f0;">{wname}</span><br>
<span style="font-size:10px;color:#475569;">로딩 중...</span>
</div>""", unsafe_allow_html=True)
        with c2:
            if st.button("✕", key=f"del_{wt}"): to_remove = wt
    if to_remove:
        st.session_state.watchlist.remove(to_remove); st.rerun()


# ── 메인 ────────────────────────────────────────────────
ticker_input = st.session_state.selected_ticker
display_name = TICKER_NAME_MAP.get(ticker_input, ticker_input.replace(".KS",""))
code_display = ticker_input.replace(".KS","")
is_korean    = ticker_input.endswith(".KS") or ticker_input.endswith(".KQ")

def fmt_p(p):
    if not p: return "N/A"
    return f"₩{int(p):,}" if is_korean else f"${p:,.2f}"

# ── 실시간 지수 티커 바 ──────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def get_market_indices():
    symbols = {
        "코스피":  "^KS11",
        "코스닥":  "^KQ11",
        "나스닥":  "^IXIC",
        "S&P500": "^GSPC",
        "다우":    "^DJI",
        "달러/원": "KRW=X",
        "엔/원":   "JPYKRW=X",
        "금":      "GC=F",
        "WTI유가": "CL=F",
    }
    results = {}
    for name, sym in symbols.items():
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=2d"
        data = _yf_get(url)
        if data:
            try:
                meta = data["chart"]["result"][0]["meta"]
                price = meta.get("regularMarketPrice", 0)
                prev  = meta.get("previousClose", price)
                chg   = ((price - prev) / prev * 100) if prev else 0
                results[name] = {"price": price, "chg": chg, "sym": sym}
            except Exception:
                pass
    return results

indices = get_market_indices()

# 티커 아이템 HTML 생성
ticker_items = []
for idx_name, val in indices.items():
    p = val["price"]
    c = val["chg"]
    color = "#22c55e" if c >= 0 else "#ef4444"
    sign  = "▲" if c >= 0 else "▼"
    if idx_name in ["달러/원", "엔/원"]:
        p_str = f"{p:,.2f}"
    elif idx_name in ["금", "WTI유가"]:
        p_str = f"${p:,.2f}"
    elif idx_name in ["코스피", "코스닥"]:
        p_str = f"{p:,.2f}"
    else:
        p_str = f"{p:,.2f}"
    item = (
        f'<span style="margin:0 32px;white-space:nowrap;">'
        f'<span style="color:#94a3b8;font-size:13px;">{idx_name}</span> '
        f'<span style="color:#f1f5f9;font-size:13px;font-weight:500;">{p_str}</span> '
        f'<span style="color:{color};font-size:12px;">{sign}{abs(c):.2f}%</span>'
        f'</span>'
    )
    ticker_items.append(item)

# 2번 반복해서 끊김 없이 스크롤
ticker_content = "".join(ticker_items * 2)

st.markdown(f"""
<style>
.ticker-wrap {{
    width: 100%;
    overflow: hidden;
    background: #0f172a;
    border: 0.5px solid #1e293b;
    border-radius: 8px;
    padding: 10px 0;
    margin-bottom: 16px;
}}
.ticker-track {{
    display: inline-flex;
    animation: ticker-scroll 30s linear infinite;
    white-space: nowrap;
}}
.ticker-wrap:hover .ticker-track {{
    animation-play-state: paused;
}}
@keyframes ticker-scroll {{
    0%   {{ transform: translateX(0); }}
    100% {{ transform: translateX(-50%); }}
}}
</style>
<div class="ticker-wrap">
  <div class="ticker-track">
    {ticker_content}
  </div>
</div>
""", unsafe_allow_html=True)

# ── 종목 헤더 + ⭐ 관심종목 버튼 ────────────────────────────
_hcol1, _hcol2 = st.columns([10, 1])
with _hcol1:
    st.markdown(f"## 📈 {display_name} ({code_display})")
with _hcol2:
    _in_watch = ticker_input in st.session_state.watchlist
    _star_label = "⭐" if _in_watch else "☆"
    _star_help  = "관심종목 제거" if _in_watch else "관심종목 추가"
    if st.button(_star_label, key="btn_star", help=_star_help, use_container_width=True):
        if _in_watch:
            st.session_state.watchlist.remove(ticker_input)
        else:
            st.session_state.watchlist.append(ticker_input)
        st.rerun()

with st.spinner("데이터 불러오는 중..."):
    info = get_stock_info(ticker_input)
if info is None:
    st.error(f"**{display_name} ({code_display})** 데이터를 불러올 수 없습니다.")
    st.info(
        "💡 **해결 방법:**\n"
        "- 장 마감(오후 3:30) 후나 주말엔 일부 종목이 조회 안 될 수 있어요\n"
        "- 검색창에서 종목코드 **6자리 숫자만** 입력해서 다시 조회해보세요\n"
        f"- 현재 코드: `{code_display}` → 올바른 코드인지 확인해보세요"
    )
    # 다른 종목 빠른 선택
    alt_tickers = ["005930.KS","000660.KS","035420.KS","005380.KS","068270.KS"]
    st.markdown("**빠른 조회:**")
    alt_cols = st.columns(len(alt_tickers))
    for i, t in enumerate(alt_tickers):
        n = TICKER_NAME_MAP.get(t, t.replace(".KS",""))
        with alt_cols[i]:
            if st.button(n, key=f"alt_{t}"):
                st.session_state.selected_ticker = t
                st.rerun()
    st.stop()

price   = info.get("currentPrice") or info.get("regularMarketPrice",0)
chg_pct = info.get("regularMarketChangePercent",0)
mkt_cap = info.get("marketCap",0)
volume  = info.get("regularMarketVolume",0)
high_52 = info.get("fiftyTwoWeekHigh",0)
low_52  = info.get("fiftyTwoWeekLow",0)
pe      = info.get("trailingPE",0)
name    = info.get("longName") or info.get("shortName",display_name)

# 메트릭 카드 글자 크기 줄이기
st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 14px !important; }
[data-testid="stMetricLabel"] { font-size: 11px !important; }
[data-testid="stMetricDelta"] { font-size: 11px !important; }
</style>
""", unsafe_allow_html=True)

c1,c2,c3,c4,c5,c6 = st.columns(6)
_chg_label = f"{chg_pct:+.2f}%" if chg_pct != 0 else "전일 동일"
c1.metric("현재가", fmt_p(price), _chg_label)
c2.metric("시가총액", format_cap(mkt_cap))
c3.metric("거래량",  f"{volume/1e4:.0f}만주" if (volume and is_korean) else (f"{volume/1e6:.1f}M" if volume else "N/A"))
c4.metric("52주 최고", fmt_p(high_52) if high_52 else "N/A")
c5.metric("52주 최저", fmt_p(low_52)  if low_52  else "N/A")
c6.metric("P/E 비율",  f"{pe:.1f}" if pe else "N/A")

st.markdown("---")
# ── 차트/포트폴리오 비율 조절 ──────────────────────────
if "col_ratio" not in st.session_state: st.session_state.col_ratio = 7
_cr1, _cr2, _cr3 = st.columns([1, 6, 1])
with _cr1: st.markdown("<p style='font-size:11px;color:#475569;margin-top:8px;'>◀ 넓게</p>", unsafe_allow_html=True)
with _cr2:
    st.session_state.col_ratio = st.slider(
        "창 크기", 4, 9,
        st.session_state.col_ratio,
        key="col_ratio_slider", label_visibility="collapsed"
    )
with _cr3: st.markdown("<p style='font-size:11px;color:#475569;margin-top:8px;'>좁게 ▶</p>", unsafe_allow_html=True)
_cr = st.session_state.col_ratio
col_chart, col_port = st.columns([_cr, 10 - _cr])

with col_chart:
    # ── 기간 버튼 ──
    period_map = {"일":"3mo","주":"1y","월":"5y","년":"10y"}
    pcols = st.columns(len(period_map))
    for i,(label,_) in enumerate(period_map.items()):
        with pcols[i]:
            btype = "primary" if st.session_state.chart_period==label else "secondary"
            if st.button(label, key=f"period_{label}", use_container_width=True, type=btype):
                st.session_state.chart_period = label; st.rerun()
    plabel = st.session_state.chart_period
    if plabel not in period_map: st.session_state.chart_period="일"; plabel="일"
    unit = {"일":"일","주":"주","월":"개월","년":"년"}[plabel]

    # ── 설정 탭 ──
    tab_ma, tab_vp, tab_ind, tab_draw = st.tabs(["📈 이동평균선","📊 매물대","🔬 보조지표","✏️ 그리기"])

    with tab_ma:
        st.markdown("""
<style>
[data-testid="stNumberInput"] input { height: 26px !important; padding: 2px 6px !important; font-size: 12px !important; }
[data-testid="stNumberInput"] button { height: 26px !important; width: 22px !important; padding: 0 !important; font-size: 12px !important; }
[data-testid="stColorPicker"] > div > div { height: 26px !important; width: 36px !important; }
</style>""", unsafe_allow_html=True)
        with st.expander("⚙️ 이동평균선 설정", expanded=False):
            new_ma = []
            for idx, ma in enumerate(st.session_state.ma_settings):
                c1,c2,c3,c4 = st.columns([1,1,3,1])
                with c1:
                    show = st.checkbox("", value=ma["show"], key=f"ma_show_{idx}")
                with c2:
                    st.markdown(f"<p style='font-size:11px;color:#94a3b8;margin:4px 0 0;'>MA{idx+1}</p>", unsafe_allow_html=True)
                with c3:
                    win = st.number_input(f"기간({unit})", min_value=1, max_value=500,
                                          value=ma["window"], key=f"ma_win_{idx}",
                                          label_visibility="collapsed")
                with c4:
                    col = st.color_picker("", value=ma["color"], key=f"ma_col_{idx}",
                                          label_visibility="collapsed")
                new_ma.append({"window":win,"color":col,"show":show})
            bc1,bc2 = st.columns(2)
            if bc1.button("+ 추가", key="add_ma"):
                st.session_state.ma_settings.append({"window":200,"color":"#22D3EE","show":True}); st.rerun()
            if bc2.button("− 삭제", key="del_ma") and len(st.session_state.ma_settings)>1:
                st.session_state.ma_settings.pop(); st.rerun()
            st.session_state.ma_settings = new_ma

    with tab_vp:
        st.caption("매물대 구간 수와 색상을 설정하세요")
        vp = st.session_state.vp_settings
        v1,v2 = st.columns(2)
        vp_show  = v1.checkbox("매물대 표시", value=vp["show"], key="vp_show")
        vp_bins  = v2.number_input("구간 수", min_value=5, max_value=50, value=vp["bins"], key="vp_bins")
        v3,v4 = st.columns(2)
        vp_above = v3.color_picker("현재가 위 색상", value=vp["color_above"], key="vp_above")
        vp_below = v4.color_picker("현재가 아래 색상", value=vp["color_below"], key="vp_below")
        st.session_state.vp_settings = {"bins":vp_bins,"color_above":vp_above,"color_below":vp_below,"show":vp_show}

    with tab_ind:
        st.caption("최대 3개까지 선택 (볼린저밴드는 메인 차트에 오버레이)")
        ind_opts = ["MACD","RSI","볼린저밴드","스토캐스틱","OBV","CCI","Williams %R","ATR"]
        selected_inds = st.multiselect("지표 선택", ind_opts,
                                       default=st.session_state.indicators,
                                       max_selections=3, key="ind_select")
        st.session_state.indicators = selected_inds

    with tab_draw:
        draw_mode = st.selectbox("도구", ["없음","추세선","수평선"], key="draw_sel")
        if draw_mode == "추세선":
            d1,d2,d3,d4,d5 = st.columns([2,2,2,2,1])
            lx0 = d1.date_input("시작일", key="lx0")
            ly0 = d2.number_input("시작가", min_value=0, value=int(price) if price else 0, step=100, key="ly0")
            lx1 = d3.date_input("끝날짜", key="lx1")
            ly1 = d4.number_input("끝가격", min_value=0, value=int(price) if price else 0, step=100, key="ly1")
            with d5:
                st.markdown("<div style='margin-top:26px'>", unsafe_allow_html=True)
                if st.button("추가", key="add_trend"):
                    st.session_state.drawn_lines.append({"type":"trend","x0":str(lx0),"y0":ly0,"x1":str(lx1),"y1":ly1,"color":"#F5A623"})
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        elif draw_mode == "수평선":
            h1,h2 = st.columns([5,1])
            hp = h1.number_input("가격", min_value=0, value=int(price) if price else 0, step=100, key="hprice")
            with h2:
                st.markdown("<div style='margin-top:26px'>", unsafe_allow_html=True)
                if st.button("추가", key="add_hline"):
                    st.session_state.drawn_lines.append({"type":"hline","y":hp,"color":"#A78BFA"}); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        if st.session_state.drawn_lines:
            if st.button(f"선 전체 삭제 ({len(st.session_state.drawn_lines)}개)", key="clear_lines"):
                st.session_state.drawn_lines = []; st.rerun()

    # ── 차트 크기 슬라이더 ──────────────────────────────
    _rh_col, _rv_col = st.columns([6,1])
    with _rh_col:
        st.session_state.chart_height = st.slider(
            "📐 차트 높이", 300, 1200,
            st.session_state.get("chart_height", 500),
            step=50, key="sl_chart_h", label_visibility="visible"
        )
    with _rv_col:
        st.markdown(f"<p style='font-size:12px;color:#94a3b8;margin-top:28px;text-align:center;'>{st.session_state.chart_height}px</p>", unsafe_allow_html=True)

    # ── 데이터 로딩 & 리샘플 ──
    hist_raw = get_history(ticker_input, period_map[plabel])
    if not hist_raw.empty:
        hist = hist_raw.copy()
        if plabel=="주":   hist = hist.resample("W").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna()
        elif plabel=="월": hist = hist.resample("ME").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna()
        elif plabel=="년": hist = hist.resample("YE").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna()

        # MA 계산
        for idx,ma in enumerate(st.session_state.ma_settings):
            hist[f"_MA{idx}"] = hist["Close"].rolling(ma["window"]).mean()

        # 매물대 계산
        vp_cfg = st.session_state.vp_settings
        NVP = vp_cfg["bins"]
        pmin,pmax = hist["Low"].min(), hist["High"].max()
        bsz = (pmax-pmin)/NVP
        vp_data = []
        for i in range(NVP):
            lo,hi = pmin+i*bsz, pmin+(i+1)*bsz
            vol = hist[(hist["Close"]>=lo)&(hist["Close"]<hi)]["Volume"].sum()
            vp_data.append({"lo":lo,"hi":hi,"mid":(lo+hi)/2,"vol":vol})
        vp_df  = pd.DataFrame(vp_data)
        vp_max = vp_df["vol"].max() if vp_df["vol"].max()>0 else 1
        x_end  = hist.index[-1]; x_start = hist.index[0]
        tot_days = max((x_end-x_start).days,1)
        vp_mw    = int(tot_days*0.15)

        # 보조지표 계산
        inds = st.session_state.indicators
        if "볼린저밴드" in inds:
            hist["_BB_mid"]   = hist["Close"].rolling(20).mean()
            hist["_BB_std"]   = hist["Close"].rolling(20).std()
            hist["_BB_upper"] = hist["_BB_mid"]+2*hist["_BB_std"]
            hist["_BB_lower"] = hist["_BB_mid"]-2*hist["_BB_std"]
        if "MACD" in inds:
            e1=hist["Close"].ewm(span=12,adjust=False).mean()
            e2=hist["Close"].ewm(span=26,adjust=False).mean()
            hist["_MACD"]=e1-e2
            hist["_MACD_sig"]=hist["_MACD"].ewm(span=9,adjust=False).mean()
            hist["_MACD_hist"]=hist["_MACD"]-hist["_MACD_sig"]
        if "RSI" in inds:
            d=hist["Close"].diff()
            gain=d.clip(lower=0).rolling(14).mean()
            loss=(-d.clip(upper=0)).rolling(14).mean()
            hist["_RSI"]=100-(100/(1+gain/loss.replace(0,float("nan"))))
        if "스토캐스틱" in inds:
            lo14=hist["Low"].rolling(14).min(); hi14=hist["High"].rolling(14).max()
            hist["_STOCH_K"]=100*(hist["Close"]-lo14)/(hi14-lo14+1e-9)
            hist["_STOCH_D"]=hist["_STOCH_K"].rolling(3).mean()
        if "OBV" in inds:
            obv=[0]
            for i in range(1,len(hist)):
                if hist["Close"].iloc[i]>hist["Close"].iloc[i-1]: obv.append(obv[-1]+hist["Volume"].iloc[i])
                elif hist["Close"].iloc[i]<hist["Close"].iloc[i-1]: obv.append(obv[-1]-hist["Volume"].iloc[i])
                else: obv.append(obv[-1])
            hist["_OBV"]=obv
        if "CCI" in inds:
            tp=(hist["High"]+hist["Low"]+hist["Close"])/3
            hist["_CCI"]=(tp-tp.rolling(20).mean())/(0.015*tp.rolling(20).std())
        if "Williams %R" in inds:
            hi14=hist["High"].rolling(14).max(); lo14=hist["Low"].rolling(14).min()
            hist["_WILLR"]=-100*(hi14-hist["Close"])/(hi14-lo14+1e-9)
        if "ATR" in inds:
            tr=pd.concat([hist["High"]-hist["Low"],(hist["High"]-hist["Close"].shift()).abs(),(hist["Low"]-hist["Close"].shift()).abs()],axis=1).max(axis=1)
            hist["_ATR"]=tr.rolling(14).mean()

        UP="#3182F6"; DN="#F04452"

        # ── 메인 차트 ──
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=hist.index, open=hist["Open"], high=hist["High"], low=hist["Low"], close=hist["Close"],
            name="캔들",
            increasing=dict(line=dict(color=UP,width=1),fillcolor=UP),
            decreasing=dict(line=dict(color=DN,width=1),fillcolor=DN),
            whiskerwidth=0.5,
            hovertext=[f"시가 {format_price(o)}<br>고가 {format_price(h)}<br>저가 {format_price(l)}<br>종가 {format_price(c)}"
                       for o,h,l,c in zip(hist["Open"],hist["High"],hist["Low"],hist["Close"])],
            hoverinfo="text+x",
        ))

        # 볼린저밴드 오버레이
        if "볼린저밴드" in inds:
            fig.add_trace(go.Scatter(x=hist.index,y=hist["_BB_upper"],mode="lines",
                line=dict(color="rgba(100,200,255,0.6)",width=1,dash="dot"),name="BB상단"))
            fig.add_trace(go.Scatter(x=hist.index,y=hist["_BB_mid"],mode="lines",
                line=dict(color="rgba(100,200,255,0.4)",width=1),name="BB중간"))
            fig.add_trace(go.Scatter(x=hist.index,y=hist["_BB_lower"],mode="lines",
                line=dict(color="rgba(100,200,255,0.6)",width=1,dash="dot"),
                fill="tonexty",fillcolor="rgba(100,200,255,0.03)",name="BB하단"))

        # MA 라인
        for idx,ma in enumerate(st.session_state.ma_settings):
            if not ma["show"]: continue
            v = hist[f"_MA{idx}"].dropna()
            if not v.empty:
                fig.add_trace(go.Scatter(x=hist.index,y=hist[f"_MA{idx}"],mode="lines",
                    line=dict(color=ma["color"],width=1.3),name=f"MA{ma['window']}",
                    hovertemplate=f"MA{ma['window']}: ₩%{{y:,.0f}}<extra></extra>"))

        # 매물대 (Scatter fill — 줌 완전 연동)
        if vp_cfg["show"]:
            cur = hist["Close"].iloc[-1]
            for _,row in vp_df.iterrows():
                if row["vol"]==0: continue
                bd = max(int(vp_mw*row["vol"]/vp_max),1)
                bex = x_end-pd.Timedelta(days=bd)
                ia  = row["mid"]>=cur
                fc  = hex_to_rgba(vp_cfg["color_above"] if ia else vp_cfg["color_below"], "0.55" if ia else "0.30")
                fig.add_trace(go.Scatter(
                    x=[bex,x_end,x_end,bex,bex],y=[row["lo"],row["lo"],row["hi"],row["hi"],row["lo"]],
                    fill="toself",fillcolor=fc,line=dict(width=0),mode="lines",showlegend=False,hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=[x_start,x_end],y=[cur,cur],mode="lines",
                line=dict(color=UP,width=1,dash="dot"),showlegend=False,
                hovertemplate=f"현재가: {format_price(cur)}<extra></extra>"))

        # 사용자 선
        for ln in st.session_state.drawn_lines:
            if ln["type"]=="trend":
                fig.add_trace(go.Scatter(x=[ln["x0"],ln["x1"]],y=[ln["y0"],ln["y1"]],
                    mode="lines",line=dict(color=ln["color"],width=1.5),showlegend=False,
                    hovertemplate="₩%{y:,.0f}<extra>추세선</extra>"))
            elif ln["type"]=="hline":
                fig.add_trace(go.Scatter(x=[x_start,x_end],y=[ln["y"],ln["y"]],
                    mode="lines",line=dict(color=ln["color"],width=1.5,dash="dash"),showlegend=False,
                    hovertemplate=f"{format_price(ln['y'])}<extra>수평선</extra>"))

        tf = {"일":"%m.%d","주":"%y.%m.%d","월":"%y.%m","년":"%Y"}.get(plabel,"%m.%d")
        chart_height = st.session_state.get("chart_height", 500)
        fig.update_layout(
            height=chart_height,margin=dict(l=0,r=90,t=10,b=0),
            plot_bgcolor="#0E1117",paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False,zeroline=False,showline=False,
                       tickfont=dict(size=11,color="#666"),tickformat=tf,rangeslider=dict(visible=False)),
            yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)",zeroline=False,showline=False,
                       tickfont=dict(size=11,color="#666"),tickformat=",",side="right"),
            hovermode="x unified",dragmode="pan",
            legend=dict(orientation="h",y=1.02,x=0,font=dict(size=11,color="#aaa"),bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig,use_container_width=True,config={
            "displayModeBar":True,
            "modeBarButtonsToRemove":["lasso2d","select2d","autoScale2d","zoom2d"],
            "displaylogo":False,"scrollZoom":True})

        # 거래량
        vol_height = st.session_state.get("vol_height", 80)
        vc=[UP if c>=o else DN for c,o in zip(hist["Close"],hist["Open"])]
        fv=go.Figure()
        fv.add_trace(go.Bar(x=hist.index,y=hist["Volume"],marker_color=vc,
            hovertemplate="<b>%{x|%Y.%m.%d}</b><br>%{y:,.0f}주<extra></extra>"))
        fv.update_layout(height=vol_height,margin=dict(l=0,r=90,t=0,b=0),
            plot_bgcolor="#0E1117",paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False,showticklabels=False,zeroline=False),
            yaxis=dict(showgrid=False,showticklabels=False,zeroline=False,side="right"),
            showlegend=False,bargap=0.15)
        st.plotly_chart(fv,use_container_width=True,config={"displayModeBar":False})

        # ── 보조지표 서브차트 ──
        def sub_layout(h=None):
            h = h or st.session_state.get("sub_height", 160)
            return dict(height=h,margin=dict(l=0,r=90,t=24,b=0),
                plot_bgcolor="#0E1117",paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False,zeroline=False,showline=False,
                           tickfont=dict(size=10,color="#555"),tickformat=tf),
                yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)",
                           zeroline=False,tickfont=dict(size=10,color="#555"),side="right"),
                hovermode="x unified",showlegend=True,
                legend=dict(orientation="h",y=1.2,x=0,font=dict(size=10,color="#aaa"),bgcolor="rgba(0,0,0,0)"))

        if "MACD" in inds:
            st.caption("▸ MACD (12·26·9)")
            fm=go.Figure()
            bc=["#3182F6" if v>=0 else "#F04452" for v in hist["_MACD_hist"].fillna(0)]
            fm.add_trace(go.Bar(x=hist.index,y=hist["_MACD_hist"],marker_color=bc,name="히스토그램",hovertemplate="%{y:.2f}<extra>히스토그램</extra>"))
            fm.add_trace(go.Scatter(x=hist.index,y=hist["_MACD"],mode="lines",line=dict(color="#3182F6",width=1.2),name="MACD",hovertemplate="MACD: %{y:.2f}<extra></extra>"))
            fm.add_trace(go.Scatter(x=hist.index,y=hist["_MACD_sig"],mode="lines",line=dict(color="#F04452",width=1.2),name="시그널",hovertemplate="시그널: %{y:.2f}<extra></extra>"))
            fm.update_layout(**sub_layout())
            st.plotly_chart(fm,use_container_width=True,config={"displayModeBar":False})

        if "RSI" in inds:
            st.caption("▸ RSI (14) — 과매수 70 / 과매도 30")
            fr=go.Figure()
            fr.add_trace(go.Scatter(x=hist.index,y=hist["_RSI"],mode="lines",line=dict(color="#F5C518",width=1.5),name="RSI",hovertemplate="RSI: %{y:.1f}<extra></extra>"))
            fr.add_hline(y=70,line=dict(color="#F04452",width=0.8,dash="dot"))
            fr.add_hline(y=30,line=dict(color="#3182F6",width=0.8,dash="dot"))
            fr.update_layout(**sub_layout()); fr.update_yaxes(range=[0,100])
            st.plotly_chart(fr,use_container_width=True,config={"displayModeBar":False})

        if "스토캐스틱" in inds:
            st.caption("▸ 스토캐스틱 (K:14 D:3) — 과매수 80 / 과매도 20")
            fs=go.Figure()
            fs.add_trace(go.Scatter(x=hist.index,y=hist["_STOCH_K"],mode="lines",line=dict(color="#C084FC",width=1.3),name="%K",hovertemplate="%%K: %{y:.1f}<extra></extra>"))
            fs.add_trace(go.Scatter(x=hist.index,y=hist["_STOCH_D"],mode="lines",line=dict(color="#F5A623",width=1.3),name="%D",hovertemplate="%%D: %{y:.1f}<extra></extra>"))
            fs.add_hline(y=80,line=dict(color="#F04452",width=0.8,dash="dot"))
            fs.add_hline(y=20,line=dict(color="#3182F6",width=0.8,dash="dot"))
            fs.update_layout(**sub_layout()); fs.update_yaxes(range=[0,100])
            st.plotly_chart(fs,use_container_width=True,config={"displayModeBar":False})

        if "OBV" in inds:
            st.caption("▸ OBV")
            fo=go.Figure()
            fo.add_trace(go.Scatter(x=hist.index,y=hist["_OBV"],mode="lines",line=dict(color="#22D3EE",width=1.3),name="OBV",hovertemplate="OBV: %{y:,.0f}<extra></extra>"))
            fo.update_layout(**sub_layout())
            st.plotly_chart(fo,use_container_width=True,config={"displayModeBar":False})

        if "CCI" in inds:
            st.caption("▸ CCI (20) — 과매수 +100 / 과매도 -100")
            fc2=go.Figure()
            fc2.add_trace(go.Scatter(x=hist.index,y=hist["_CCI"],mode="lines",line=dict(color="#34D399",width=1.3),name="CCI",hovertemplate="CCI: %{y:.1f}<extra></extra>"))
            fc2.add_hline(y=100,line=dict(color="#F04452",width=0.8,dash="dot"))
            fc2.add_hline(y=-100,line=dict(color="#3182F6",width=0.8,dash="dot"))
            fc2.update_layout(**sub_layout())
            st.plotly_chart(fc2,use_container_width=True,config={"displayModeBar":False})

        if "Williams %R" in inds:
            st.caption("▸ Williams %R (14) — 과매수 -20 / 과매도 -80")
            fw=go.Figure()
            fw.add_trace(go.Scatter(x=hist.index,y=hist["_WILLR"],mode="lines",line=dict(color="#FB923C",width=1.3),name="W%R",hovertemplate="W%%R: %{y:.1f}<extra></extra>"))
            fw.add_hline(y=-20,line=dict(color="#F04452",width=0.8,dash="dot"))
            fw.add_hline(y=-80,line=dict(color="#3182F6",width=0.8,dash="dot"))
            fw.update_layout(**sub_layout()); fw.update_yaxes(range=[-100,0])
            st.plotly_chart(fw,use_container_width=True,config={"displayModeBar":False})

        if "ATR" in inds:
            st.caption("▸ ATR (14) — 변동성 지표")
            fa=go.Figure()
            fa.add_trace(go.Scatter(x=hist.index,y=hist["_ATR"],mode="lines",line=dict(color="#A78BFA",width=1.3),name="ATR",hovertemplate="ATR: ₩%{y:,.0f}<extra></extra>"))
            fa.update_layout(**sub_layout())
            st.plotly_chart(fa,use_container_width=True,config={"displayModeBar":False})

    else:
        st.info("차트 데이터를 불러올 수 없습니다.")

# ── 포트폴리오 ──────────────────────────────────────────
with col_port:
    st.markdown("### 💼 포트폴리오")
    with st.form("add_portfolio"):
        pa,pb,pc = st.columns([2,1,1])
        p_ticker = pa.text_input("종목코드 (6자리)", value=code_display)
        p_shares = pb.number_input("수량", min_value=1, value=10)
        p_price2 = pc.number_input("매수가", min_value=1.0, value=float(price) if price else 1000.0, step=100.0)
        if st.form_submit_button("추가", use_container_width=True):
            code = p_ticker.strip().zfill(6)+".KS"
            st.session_state.portfolio.append({"ticker":code,"shares":p_shares,"avg_price":p_price2})
            st.rerun()
    if st.session_state.portfolio:
        ti=tv=0; rows=[]
        for item in st.session_state.portfolio:
            ci = get_stock_info(item["ticker"])
            cp = (ci.get("currentPrice") or ci.get("regularMarketPrice",item["avg_price"])) if ci else item["avg_price"]
            inv=item["avg_price"]*item["shares"]; val=cp*item["shares"]
            pnl=val-inv; pp=(pnl/inv*100) if inv else 0
            ti+=inv; tv+=val
            pname=TICKER_NAME_MAP.get(item["ticker"],item["ticker"].replace(".KS",""))
            rows.append({"종목":pname,"수량":item["shares"],"매수가":format_price(item["avg_price"]),
                         "현재가":format_price(cp),"손익":f"₩{pnl:+,.0f} ({pp:+.1f}%)"})
        st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
        tp=tv-ti; tpct=(tp/ti*100) if ti else 0
        st.metric("총 평가손익",f"₩{tp:+,.0f}",f"{tpct:+.2f}%")
        if st.button("포트폴리오 초기화"):
            st.session_state.portfolio=[]; st.rerun()
    else:
        st.info("종목을 추가해보세요.")

st.markdown("---")
col_news, col_ai = st.columns([1, 1])

# ── 📰 주요 뉴스 (RSS — API 키 불필요) ───────────────────
with col_news:
    st.markdown("### 📰 주요 뉴스")

    @st.cache_data(ttl=600, show_spinner=False)
    def get_rss_news(stock_name, ticker):
        """네이버/구글 뉴스 RSS로 뉴스 가져오기 — API 키 불필요"""
        import urllib.request, urllib.parse
        from xml.etree import ElementTree as ET

        is_kr = ticker.endswith(".KS") or ticker.endswith(".KQ")
        code  = ticker.replace(".KS","").replace(".KQ","")
        results = []

        # 검색어 목록 (한국어 우선, 영어 포함)
        queries = [stock_name, code] if is_kr else [stock_name, code]

        for q in queries:
            if len(results) >= 5:
                break
            try:
                # 네이버 뉴스 RSS (한국 종목)
                if is_kr:
                    enc_q = urllib.parse.quote(q)
                    url = f"https://news.naver.com/search/News?query={enc_q}&sort=1&field=1&where=news&section=101&rss=1"
                    try:
                        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
                        with urllib.request.urlopen(req, timeout=5) as r:
                            tree = ET.parse(r)
                        root = tree.getroot()
                        ch = root.find("channel")
                        if ch is not None:
                            for item in ch.findall("item")[:5]:
                                title = item.findtext("title","").replace("<b>","").replace("</b>","")
                                link  = item.findtext("link","#")
                                pub   = item.findtext("pubDate","")[:16] if item.findtext("pubDate") else ""
                                desc  = item.findtext("description","").replace("<b>","").replace("</b>","")[:60]
                                source = item.findtext("source", "네이버뉴스")
                                if title:
                                    results.append({"title":title,"link":link,"date":pub,"summary":desc,"source":source})
                    except Exception:
                        pass

                # 구글 뉴스 RSS
                enc_q2 = urllib.parse.quote(f"{q} 주식" if is_kr else f"{q} stock")
                hl = "ko" if is_kr else "en"
                gl = "KR" if is_kr else "US"
                url2 = f"https://news.google.com/rss/search?q={enc_q2}&hl={hl}&gl={gl}&ceid={gl}:{hl}"
                req2 = urllib.request.Request(url2, headers={"User-Agent":"Mozilla/5.0"})
                with urllib.request.urlopen(req2, timeout=5) as r2:
                    tree2 = ET.parse(r2)
                root2 = tree2.getroot()
                ch2 = root2.find("channel")
                if ch2 is not None:
                    for item in ch2.findall("item")[:5]:
                        title = item.findtext("title","")
                        link  = item.findtext("link","#")
                        pub   = item.findtext("pubDate","")[:16] if item.findtext("pubDate") else ""
                        source = item.findtext("source","Google 뉴스")
                        if title and title not in [r["title"] for r in results]:
                            results.append({"title":title,"link":link,"date":pub,"summary":"","source":source})
            except Exception:
                continue

        return results[:5]

    with st.spinner("뉴스 불러오는 중..."):
        _rss_news = get_rss_news(display_name, ticker_input)

    if _rss_news:
        for _ni in _rss_news:
            _title  = _ni.get("title","")
            _link   = _ni.get("link","#")
            _src    = _ni.get("source","")
            _dt     = _ni.get("date","")
            _summ   = _ni.get("summary","")
            st.markdown(f"""
<div style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
  <a href="{_link}" target="_blank"
     style="color:#e2e8f0;font-size:12px;font-weight:500;text-decoration:none;line-height:1.5;display:block;margin-bottom:3px;">
    {_title}
  </a>
  <span style="color:#475569;font-size:11px;">{_src}{" · " + _dt[:10] if _dt else ""}</span>
  {f'<p style="color:#64748b;font-size:11px;margin:3px 0 0;">{_summ}</p>' if _summ else ''}
</div>""", unsafe_allow_html=True)
        st.caption(f"📡 RSS 뉴스 · {datetime.today().strftime('%m/%d %H:%M')} 기준")
        if st.button("🔄 새로고침", key="refresh_news"):
            get_rss_news.clear(); st.rerun()
    else:
        st.info("뉴스를 불러올 수 없습니다. 🔄 새로고침을 눌러보세요.")
        if st.button("🔄 새로고침", key="refresh_news_retry"):
            get_rss_news.clear(); st.rerun()

# ── 🤖 AI 주식 분석 (Gem 스타일 대화형) ─────────────────
with col_ai:
    st.markdown("### 🤖 AI 주식 분석")

    try: _ai_key = st.secrets.get("GEMINI_API_KEY","")
    except Exception: _ai_key=""

    # 대화 히스토리 초기화
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_ticker" not in st.session_state:
        st.session_state.chat_ticker = ""

    # 종목 바뀌면 대화 초기화
    if st.session_state.chat_ticker != ticker_input:
        st.session_state.chat_history = []
        st.session_state.chat_ticker  = ticker_input

    # 시스템 컨텍스트 (현재 종목 정보 자동 포함)
    _is_kr = ticker_input.endswith(".KS") or ticker_input.endswith(".KQ")
    _port_summary = ", ".join([
        f"{TICKER_NAME_MAP.get(p['ticker'],p['ticker'].replace('.KS',''))} {p['shares']}주"
        for p in st.session_state.portfolio
    ]) or "없음"
    _stock_ctx = f"""현재 조회 종목: {display_name} ({code_display})
현재가: {fmt_p(price)} | 등락률: {chg_pct:+.2f}% | 시가총액: {format_cap(mkt_cap)}
52주 범위: {fmt_p(low_52)} ~ {fmt_p(high_52)} | P/E: {f"{pe:.1f}" if pe else "N/A"}
보유 포트폴리오: {_port_summary}"""

    _system_prompt = f"""당신은 전문 주식 분석가 AI입니다. 사용자의 투자 결정을 돕는 명확하고 실용적인 분석을 제공합니다.

{_stock_ctx}

분석 원칙:
- 데이터 기반의 객관적 분석 제공
- 투자 위험 항상 언급
- 한국어로 친절하게 답변
- 핵심을 간결하게 전달 (너무 길지 않게)
- 매수/매도 의견 제시 시 근거 명확히 설명"""

    # 대화창 표시
    _chat_container = st.container(height=380)
    with _chat_container:
        if not st.session_state.chat_history:
            st.markdown(f"""
<div style="text-align:center;padding:30px 20px;color:#475569;">
  <div style="font-size:28px;margin-bottom:12px;">🤖</div>
  <p style="font-size:13px;font-weight:500;color:#94a3b8;margin:0 0 6px;">{display_name} AI 분석가</p>
  <p style="font-size:12px;color:#475569;margin:0;">종목에 대해 무엇이든 물어보세요</p>
</div>
<div style="display:flex;flex-wrap:wrap;gap:6px;justify-content:center;padding:0 10px;">
  <span style="background:#1e293b;color:#94a3b8;font-size:11px;padding:5px 10px;border-radius:20px;cursor:pointer;">지금 매수 타이밍인가요?</span>
  <span style="background:#1e293b;color:#94a3b8;font-size:11px;padding:5px 10px;border-radius:20px;cursor:pointer;">현재 주가 고평가인가요?</span>
  <span style="background:#1e293b;color:#94a3b8;font-size:11px;padding:5px 10px;border-radius:20px;cursor:pointer;">리스크 요인을 알려주세요</span>
</div>""", unsafe_allow_html=True)
        else:
            for _msg in st.session_state.chat_history:
                if _msg["role"] == "user":
                    st.markdown(f"""
<div style="display:flex;justify-content:flex-end;margin-bottom:10px;">
  <div style="background:#1e40af;color:#fff;font-size:12px;padding:8px 12px;border-radius:12px 12px 2px 12px;max-width:85%;line-height:1.5;">{_msg['content']}</div>
</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
<div style="display:flex;gap:8px;margin-bottom:10px;align-items:flex-start;">
  <div style="width:24px;height:24px;background:#0f172a;border:1px solid #1e293b;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0;">🤖</div>
  <div style="background:#0d1526;border:1px solid #1e293b;color:#e2e8f0;font-size:12px;padding:8px 12px;border-radius:2px 12px 12px 12px;max-width:90%;line-height:1.6;">{_msg['content']}</div>
</div>""", unsafe_allow_html=True)

    # 입력창
    _q_col, _btn_col = st.columns([5, 1])
    with _q_col:
        _question = st.text_input("질문 입력", placeholder=f"{display_name}에 대해 질문하세요...",
                                  key="chat_input", label_visibility="collapsed")
    with _btn_col:
        _send = st.button("전송", key="chat_send", use_container_width=True, type="primary")

    # 빠른 질문 버튼
    _qcols = st.columns(3)
    _quick_qs = ["매수 타이밍?", "고평가 여부?", "주요 리스크?"]
    for _qi, (_qc, _qq) in enumerate(zip(_qcols, _quick_qs)):
        with _qc:
            if st.button(_qq, key=f"quick_{_qi}", use_container_width=True):
                _question = _qq
                _send = True

    # 전송 처리
    if _send and _question.strip():
        if not _ai_key:
            st.warning("GEMINI_API_KEY를 Secrets에 설정해주세요.")
        else:
            st.session_state.chat_history.append({"role":"user","content":_question.strip()})
            with st.spinner("분석 중..."):
                try:
                    import google.generativeai as genai2
                    genai2.configure(api_key=_ai_key)
                    _model = genai2.GenerativeModel(
                        model_name="gemini-2.0-flash",
                        system_instruction=_system_prompt
                    )
                    # 대화 히스토리 포함해서 전송
                    _history_text = ""
                    for _h in st.session_state.chat_history[:-1][-6:]:  # 최근 6개만
                        _role = "사용자" if _h["role"]=="user" else "AI"
                        _history_text += _role + ": " + _h["content"] + "\n"
                    _full_prompt = f"{_history_text}사용자: {_question.strip()}"
                    _resp = _model.generate_content(_full_prompt)
                    _answer = _resp.text
                    st.session_state.chat_history.append({"role":"assistant","content":_answer})
                except Exception as e:
                    st.session_state.chat_history.append({"role":"assistant","content":f"오류: {str(e)}"})
            st.rerun()

    # 대화 초기화 버튼
    if st.session_state.chat_history:
        if st.button("🗑 대화 초기화", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()
