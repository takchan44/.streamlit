import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import google.generativeai as genai

st.set_page_config(
    page_title="코스피 주식 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 코스피 전 종목 불러오기 ─────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_kospi_stocks():
    try:
        from pykrx import stock
        # 최근 5일 중 거래일 찾기
        for i in range(5):
            from datetime import timedelta
            d = (datetime.today() - timedelta(days=i)).strftime("%Y%m%d")
            tickers = stock.get_market_ticker_list(d, market="KOSPI")
            if tickers:
                result = {}
                for code in tickers:
                    name = stock.get_market_ticker_name(code)
                    if name:
                        result[name] = code + ".KS"
                if result:
                    return result
    except Exception:
        pass
    # pykrx 실패 시 내장 목록 사용
    return BUILTIN_STOCKS

# 내장 코스피 종목 (pykrx 실패 대비)
BUILTIN_STOCKS = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS", "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS", "셀트리온": "068270.KS",
    "기아": "000270.KS", "KB금융": "105560.KS",
    "신한지주": "055550.KS", "POSCO홀딩스": "005490.KS",
    "LG화학": "051910.KS", "삼성SDI": "006400.KS",
    "현대모비스": "012330.KS", "카카오": "035720.KS",
    "NAVER": "035420.KS", "하나금융지주": "086790.KS",
    "우리금융지주": "316140.KS", "삼성물산": "028260.KS",
    "LG전자": "066570.KS", "SK이노베이션": "096770.KS",
    "SK텔레콤": "017670.KS", "KT": "030200.KS",
    "한국전력": "015760.KS", "두산에너빌리티": "034020.KS",
    "삼성생명": "032830.KS", "에코프로비엠": "247540.KS",
    "에코프로": "086520.KS", "포스코퓨처엠": "003670.KS",
    "한국조선해양": "009540.KS", "삼성중공업": "010140.KS",
    "현대중공업": "329180.KS", "HD현대": "267250.KS",
    "현대글로비스": "086280.KS", "아모레퍼시픽": "090430.KS",
    "LG생활건강": "051900.KS", "하이브": "352820.KS",
    "크래프톤": "259960.KS", "카카오뱅크": "323410.KS",
    "카카오페이": "377300.KS", "대한항공": "003490.KS",
    "현대건설": "000720.KS", "HMM": "011200.KS",
    "강원랜드": "035250.KS", "한미약품": "128940.KS",
    "유한양행": "000100.KS", "삼성전기": "009150.KS",
    "삼성SDS": "018260.KS", "SK바이오팜": "326030.KS",
    "HLB": "028300.KS", "기업은행": "024110.KS",
    "미래에셋증권": "006800.KS", "한화에어로스페이스": "012450.KS",
    "두산밥캣": "241560.KS", "고려아연": "010130.KS",
    "농심": "004370.KS", "오리온": "271560.KS",
    "CJ제일제당": "097950.KS", "하나금융지주": "086790.KS",
    "종근당": "185750.KS", "대웅제약": "069620.KS",
    "롯데쇼핑": "023530.KS", "이마트": "139480.KS",
    "GS리테일": "007070.KS", "현대백화점": "069960.KS",
    "한화솔루션": "009830.KS", "CJ ENM": "035760.KS",
    "스튜디오드래곤": "253450.KS", "엔씨소프트": "036570.KS",
    "넷마블": "251270.KS", "GS건설": "006360.KS",
    "DL이앤씨": "375500.KS", "호텔신라": "008770.KS",
    "삼성증권": "016360.KS", "NH투자증권": "005940.KS",
    "SM엔터테인먼트": "041510.KS", "JYP엔터테인먼트": "035900.KS",
    "LG": "003550.KS", "SK": "034730.KS",
    "금호석유": "011780.KS", "코웨이": "021240.KS",
}

# ── 세션 초기화 ─────────────────────────────────────────
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["005930.KS", "000660.KS", "035420.KS", "005380.KS", "068270.KS"]
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "005930.KS"
if "kospi_loaded" not in st.session_state:
    st.session_state.kospi_loaded = False

# ── 종목 리스트 로딩 ────────────────────────────────────
if not st.session_state.kospi_loaded:
    with st.spinner("코스피 전 종목 불러오는 중..."):
        KOSPI_STOCKS = load_kospi_stocks()
        st.session_state.kospi_stocks = KOSPI_STOCKS
        st.session_state.kospi_loaded = True
else:
    KOSPI_STOCKS = st.session_state.get("kospi_stocks", BUILTIN_STOCKS)

TICKER_NAME_MAP = {v: k for k, v in KOSPI_STOCKS.items()}

# ── 유틸 함수 ───────────────────────────────────────────
def format_price(price):
    if not price:
        return "N/A"
    return f"₩{int(price):,}"

def format_cap(val):
    if not val:
        return "N/A"
    if val >= 1e12:
        return f"{val/1e12:.1f}조"
    elif val >= 1e8:
        return f"{val/1e8:.0f}억"
    return f"{val/1e9:.1f}B"

# ── 데이터 함수 ─────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def get_stock_info(ticker: str):
    try:
        t = yf.Ticker(ticker)
        info = t.info

        # currentPrice 또는 regularMarketPrice 확인
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if price:
            return info

        # yfinance history로 보완
        hist = t.history(period="5d")
        if not hist.empty:
            last_close = float(hist["Close"].iloc[-1])
            info["currentPrice"] = last_close
            info["regularMarketPrice"] = last_close
            if not info.get("regularMarketVolume"):
                info["regularMarketVolume"] = int(hist["Volume"].iloc[-1])
            return info

    except Exception:
        pass

    # yfinance 완전 실패 시 pykrx로 폴백
    try:
        from pykrx import stock as krx
        code = ticker.replace(".KS", "").replace(".KQ", "")
        from datetime import timedelta
        for i in range(5):
            d = (datetime.today() - timedelta(days=i)).strftime("%Y%m%d")
            df = krx.get_market_ohlcv_by_date(d, d, code)
            if not df.empty:
                row = df.iloc[-1]
                close = float(row["종가"])
                volume = int(row["거래량"])
                # 기본 info 구조 반환
                return {
                    "currentPrice": close,
                    "regularMarketPrice": close,
                    "regularMarketVolume": volume,
                    "regularMarketChangePercent": float(row.get("등락률", 0)),
                    "regularMarketChange": float(row["종가"] - row["시가"]),
                    "fiftyTwoWeekHigh": 0,
                    "fiftyTwoWeekLow": 0,
                    "marketCap": 0,
                    "trailingPE": 0,
                    "longName": krx.get_market_ticker_name(code),
                }
    except Exception:
        pass

    return None

@st.cache_data(ttl=300, show_spinner=False)
def get_history(ticker: str, period: str):
    try:
        hist = yf.Ticker(ticker).history(period=period)
        if not hist.empty:
            return hist
    except Exception:
        pass

    # pykrx 폴백
    try:
        from pykrx import stock as krx
        from datetime import timedelta
        code = ticker.replace(".KS", "").replace(".KQ", "")
        period_days = {"5d": 7, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "5y": 1825}
        days = period_days.get(period, 90)
        end = datetime.today().strftime("%Y%m%d")
        start = (datetime.today() - timedelta(days=days)).strftime("%Y%m%d")
        df = krx.get_market_ohlcv_by_date(start, end, code)
        if not df.empty:
            df = df.rename(columns={"시가": "Open", "고가": "High", "저가": "Low", "종가": "Close", "거래량": "Volume"})
            return df[["Open", "High", "Low", "Close", "Volume"]]
    except Exception:
        pass

    return pd.DataFrame()

@st.cache_data(ttl=600, show_spinner=False)
def get_news(ticker: str):
    try:
        news = yf.Ticker(ticker).news
        return news[:5] if news else []
    except Exception:
        return []

# ── 사이드바 ────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### 🔍 종목 검색")
    st.caption(f"총 {len(KOSPI_STOCKS):,}개 종목")

    search_query = st.text_input("종목명 또는 코드", placeholder="삼성, 005930...")

    if search_query:
        q = search_query.strip().upper()
        results = {
            n: t for n, t in KOSPI_STOCKS.items()
            if q in n.upper() or q in t.replace(".KS", "")
        }
        if results:
            names = list(results.keys())
            sel = st.selectbox(
                f"검색 결과 {len(results)}개",
                options=names,
                format_func=lambda x: f"{x} ({results[x].replace('.KS','')})"
            )
            if st.button("조회", use_container_width=True, key="btn_search"):
                st.session_state.selected_ticker = results[sel]
                st.rerun()
        else:
            st.caption("검색 결과가 없습니다.")
    else:
        names = list(KOSPI_STOCKS.keys())
        # 현재 선택된 종목 기본값 설정
        current_name = TICKER_NAME_MAP.get(st.session_state.selected_ticker, names[0])
        default_idx = names.index(current_name) if current_name in names else 0

        sel = st.selectbox(
            "전체 종목",
            options=names,
            index=default_idx,
            format_func=lambda x: f"{x} ({KOSPI_STOCKS[x].replace('.KS','')})"
        )
        if st.button("조회", use_container_width=True, key="btn_list"):
            st.session_state.selected_ticker = KOSPI_STOCKS[sel]
            st.rerun()

    st.markdown("---")
    st.markdown("### ⭐ 관심 종목")
    to_remove = None
    for wt in st.session_state.watchlist:
        winfo = get_stock_info(wt)
        wname = TICKER_NAME_MAP.get(wt, wt.replace(".KS", ""))
        if winfo:
            wp = winfo.get("currentPrice") or winfo.get("regularMarketPrice", 0)
            wc = winfo.get("regularMarketChangePercent", 0)
            icon = "🟢" if wc >= 0 else "🔴"
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"{icon} **{wname}**  \n{format_price(wp)} ({wc:+.2f}%)")
            with c2:
                if st.button("✕", key=f"del_{wt}"):
                    to_remove = wt
        else:
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"⚪ **{wname}**")
            with c2:
                if st.button("✕", key=f"del_{wt}"):
                    to_remove = wt
    if to_remove:
        st.session_state.watchlist.remove(to_remove)
        st.rerun()

    st.markdown("---")
    st.caption("관심 종목 추가")
    wq = st.text_input("검색", placeholder="삼성전자, 005930", key="wq")
    if wq:
        wqr = {
            n: t for n, t in KOSPI_STOCKS.items()
            if wq.upper() in n.upper() or wq in t.replace(".KS", "")
        }
        if wqr:
            wpick = st.selectbox(
                "선택", list(wqr.keys()), key="wpick",
                format_func=lambda x: f"{x} ({wqr[x].replace('.KS','')})"
            )
            if st.button("관심 추가", use_container_width=True):
                wt = wqr.get(wpick)
                if wt and wt not in st.session_state.watchlist:
                    st.session_state.watchlist.append(wt)
                    st.rerun()

# ── 메인 화면 ───────────────────────────────────────────
ticker_input = st.session_state.selected_ticker
display_name = TICKER_NAME_MAP.get(ticker_input, ticker_input.replace(".KS", ""))
code_display = ticker_input.replace(".KS", "")

st.markdown(f"## 📈 {display_name} ({code_display})")

with st.spinner("데이터 불러오는 중..."):
    info = get_stock_info(ticker_input)

if info is None:
    st.error(f"**{display_name}** 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")
    st.info("💡 장 마감 후나 주말에는 일부 종목 데이터가 제한될 수 있습니다.")
    st.stop()

price   = info.get("currentPrice") or info.get("regularMarketPrice", 0)
chg_pct = info.get("regularMarketChangePercent", 0)
mkt_cap = info.get("marketCap", 0)
volume  = info.get("regularMarketVolume", 0)
high_52 = info.get("fiftyTwoWeekHigh", 0)
low_52  = info.get("fiftyTwoWeekLow", 0)
pe      = info.get("trailingPE", 0)
name    = info.get("longName") or info.get("shortName", display_name)

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("현재가", format_price(price), f"{chg_pct:+.2f}%")
c2.metric("시가총액", format_cap(mkt_cap))
c3.metric("거래량", f"{volume/1e4:.0f}만주" if volume else "N/A")
c4.metric("52주 최고", format_price(high_52) if high_52 else "N/A")
c5.metric("52주 최저", format_price(low_52) if low_52 else "N/A")
c6.metric("P/E 비율", f"{pe:.1f}" if pe else "N/A")

st.markdown("---")

col_chart, col_port = st.columns([2, 1])

with col_chart:
    st.markdown("### 주가 차트")
    period_map = {"1주": "5d", "1달": "1mo", "3달": "3mo", "6달": "6mo", "1년": "1y", "5년": "5y"}
    plabel = st.radio("기간", list(period_map.keys()), horizontal=True, index=2)
    hist = get_history(ticker_input, period_map[plabel])
    if not hist.empty:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=hist.index, open=hist["Open"], high=hist["High"],
            low=hist["Low"], close=hist["Close"], name=code_display,
            increasing_line_color="#1D9E75", decreasing_line_color="#E24B4A"
        ))
        fig.add_trace(go.Bar(
            x=hist.index, y=hist["Volume"], name="거래량",
            yaxis="y2", marker_color="rgba(100,130,200,0.3)"
        ))
        fig.update_layout(
            yaxis2=dict(overlaying="y", side="right", showgrid=False, title="거래량"),
            xaxis_rangeslider_visible=False, height=400,
            margin=dict(l=0, r=0, t=20, b=0),
            legend=dict(orientation="h", y=1.05)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("차트 데이터를 불러올 수 없습니다.")

with col_port:
    st.markdown("### 💼 포트폴리오")
    with st.form("add_portfolio"):
        pa, pb, pc = st.columns([2, 1, 1])
        p_ticker = pa.text_input("종목코드 (6자리)", value=code_display)
        p_shares = pb.number_input("수량", min_value=1, value=10)
        p_price  = pc.number_input("매수가", min_value=1.0, value=float(price) if price else 1000.0, step=100.0)
        if st.form_submit_button("추가", use_container_width=True):
            code = p_ticker.strip().zfill(6) + ".KS"
            st.session_state.portfolio.append({
                "ticker": code, "shares": p_shares, "avg_price": p_price
            })
            st.rerun()

    if st.session_state.portfolio:
        total_invest = total_value = 0
        rows = []
        for item in st.session_state.portfolio:
            ci = get_stock_info(item["ticker"])
            cp = (ci.get("currentPrice") or ci.get("regularMarketPrice", item["avg_price"])) if ci else item["avg_price"]
            inv = item["avg_price"] * item["shares"]
            val = cp * item["shares"]
            pnl = val - inv
            pnl_pct = (pnl / inv * 100) if inv else 0
            total_invest += inv
            total_value  += val
            pname = TICKER_NAME_MAP.get(item["ticker"], item["ticker"].replace(".KS", ""))
            rows.append({
                "종목": pname,
                "수량": item["shares"],
                "매수가": format_price(item["avg_price"]),
                "현재가": format_price(cp),
                "손익": f"₩{pnl:+,.0f} ({pnl_pct:+.1f}%)"
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        total_pnl = total_value - total_invest
        total_pct = (total_pnl / total_invest * 100) if total_invest else 0
        st.metric("총 평가손익", f"₩{total_pnl:+,.0f}", f"{total_pct:+.2f}%")
        if st.button("포트폴리오 초기화"):
            st.session_state.portfolio = []
            st.rerun()
    else:
        st.info("종목을 추가해보세요.")

st.markdown("---")

col_news, col_ai = st.columns([1, 1])

with col_news:
    st.markdown("### 📰 관련 뉴스")
    news = get_news(ticker_input)
    if news:
        for item in news:
            title     = item.get("title", "")
            link      = item.get("link", "#")
            publisher = item.get("publisher", "")
            pub_time  = item.get("providerPublishTime", 0)
            time_str  = datetime.fromtimestamp(pub_time).strftime("%m/%d %H:%M") if pub_time else ""
            st.markdown(f"**[{title}]({link})**  \n_{publisher} · {time_str}_")
            st.markdown("---")
    else:
        st.info("뉴스를 불러올 수 없습니다.")

with col_ai:
    st.markdown("### 🤖 AI 주식 분석 (Gemini)")
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        api_key = ""

    question = st.text_area("질문 입력",
        placeholder=f"예: {display_name} 지금 매수하기 좋은 타이밍인가요?", height=100)

    if st.button("AI 분석 요청 ↗", use_container_width=True):
        if not api_key:
            st.warning("Streamlit Cloud Secrets에 GEMINI_API_KEY를 설정해주세요.")
        elif not question.strip():
            st.warning("질문을 입력해주세요.")
        else:
            port_summary = ", ".join([
                f"{TICKER_NAME_MAP.get(p['ticker'], p['ticker'].replace('.KS',''))} {p['shares']}주"
                for p in st.session_state.portfolio
            ]) or "없음"
            stock_summary = f"""종목: {name} ({code_display})
현재가: {format_price(price)}
등락률: {chg_pct:+.2f}%
시가총액: {format_cap(mkt_cap)}
P/E: {f"{pe:.1f}" if pe else "N/A"}
52주 범위: {format_price(low_52)} ~ {format_price(high_52)}
포트폴리오: {port_summary}"""
            with st.spinner("Gemini가 분석 중..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        system_instruction="당신은 전문 주식 분석가입니다. 주어진 데이터를 바탕으로 명확하고 유익한 분석을 제공하세요. 모든 금액은 원화(₩) 기준으로 설명하세요. 항상 투자 위험을 언급하세요."
                    )
                    response = model.generate_content(
                        f"주식 데이터:\n{stock_summary}\n\n질문: {question}"
                    )
                    st.success(response.text)
                except Exception as e:
                    st.error(f"오류 발생: {e}")
