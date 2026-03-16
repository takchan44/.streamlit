import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
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
        for i in range(5):
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
    return BUILTIN_STOCKS

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
    "CJ제일제당": "097950.KS", "종근당": "185750.KS",
    "대웅제약": "069620.KS", "롯데쇼핑": "023530.KS",
    "이마트": "139480.KS", "GS리테일": "007070.KS",
    "현대백화점": "069960.KS", "한화솔루션": "009830.KS",
    "CJ ENM": "035760.KS", "스튜디오드래곤": "253450.KS",
    "엔씨소프트": "036570.KS", "넷마블": "251270.KS",
    "GS건설": "006360.KS", "DL이앤씨": "375500.KS",
    "호텔신라": "008770.KS", "삼성증권": "016360.KS",
    "NH투자증권": "005940.KS", "SM엔터테인먼트": "041510.KS",
    "JYP엔터테인먼트": "035900.KS", "LG": "003550.KS",
    "SK": "034730.KS", "금호석유": "011780.KS", "코웨이": "021240.KS",
}

# ── 세션 초기화 ─────────────────────────────────────────
if "portfolio"       not in st.session_state: st.session_state.portfolio = []
if "watchlist"       not in st.session_state: st.session_state.watchlist = ["005930.KS","000660.KS","035420.KS","005380.KS","068270.KS"]
if "selected_ticker" not in st.session_state: st.session_state.selected_ticker = "005930.KS"
if "kospi_loaded"    not in st.session_state: st.session_state.kospi_loaded = False
if "chart_period"    not in st.session_state: st.session_state.chart_period = "일"
if "drawn_lines"     not in st.session_state: st.session_state.drawn_lines = []

# ── 종목 로딩 ───────────────────────────────────────────
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
    if not price: return "N/A"
    return f"₩{int(price):,}"

def format_cap(val):
    if not val: return "N/A"
    if val >= 1e12: return f"{val/1e12:.1f}조"
    elif val >= 1e8: return f"{val/1e8:.0f}억"
    return f"{val/1e9:.1f}B"

# ── 데이터 함수 ─────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def get_stock_info(ticker: str):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if price:
            return info
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
    try:
        from pykrx import stock as krx
        code = ticker.replace(".KS","").replace(".KQ","")
        for i in range(5):
            d = (datetime.today() - timedelta(days=i)).strftime("%Y%m%d")
            df = krx.get_market_ohlcv_by_date(d, d, code)
            if not df.empty:
                row = df.iloc[-1]
                close = float(row["종가"])
                return {
                    "currentPrice": close, "regularMarketPrice": close,
                    "regularMarketVolume": int(row["거래량"]),
                    "regularMarketChangePercent": float(row.get("등락률", 0)),
                    "regularMarketChange": float(row["종가"] - row["시가"]),
                    "fiftyTwoWeekHigh": 0, "fiftyTwoWeekLow": 0,
                    "marketCap": 0, "trailingPE": 0,
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
    try:
        from pykrx import stock as krx
        code = ticker.replace(".KS","").replace(".KQ","")
        days = {"5d":7,"1mo":30,"3mo":90,"6mo":180,"1y":365,"5y":1825}.get(period, 90)
        end   = datetime.today().strftime("%Y%m%d")
        start = (datetime.today() - timedelta(days=days)).strftime("%Y%m%d")
        df = krx.get_market_ohlcv_by_date(start, end, code)
        if not df.empty:
            df = df.rename(columns={"시가":"Open","고가":"High","저가":"Low","종가":"Close","거래량":"Volume"})
            return df[["Open","High","Low","Close","Volume"]]
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
        results = {n: t for n, t in KOSPI_STOCKS.items() if q in n.upper() or q in t.replace(".KS","")}
        if results:
            names = list(results.keys())
            sel = st.selectbox(f"검색 결과 {len(results)}개", options=names,
                               format_func=lambda x: f"{x} ({results[x].replace('.KS','')})")
            if st.button("조회", use_container_width=True, key="btn_search"):
                st.session_state.selected_ticker = results[sel]
                st.rerun()
        else:
            st.caption("검색 결과가 없습니다.")
    else:
        names = list(KOSPI_STOCKS.keys())
        current_name = TICKER_NAME_MAP.get(st.session_state.selected_ticker, names[0])
        default_idx = names.index(current_name) if current_name in names else 0
        sel = st.selectbox("전체 종목", options=names, index=default_idx,
                           format_func=lambda x: f"{x} ({KOSPI_STOCKS[x].replace('.KS','')})")
        if st.button("조회", use_container_width=True, key="btn_list"):
            st.session_state.selected_ticker = KOSPI_STOCKS[sel]
            st.rerun()

    st.markdown("---")
    st.markdown("### ⭐ 관심 종목")
    to_remove = None
    for wt in st.session_state.watchlist:
        winfo = get_stock_info(wt)
        wname = TICKER_NAME_MAP.get(wt, wt.replace(".KS",""))
        c1, c2 = st.columns([5,1])
        if winfo:
            wp = winfo.get("currentPrice") or winfo.get("regularMarketPrice", 0)
            wc = winfo.get("regularMarketChangePercent", 0)
            icon = "🟢" if wc >= 0 else "🔴"
            with c1: st.markdown(f"{icon} **{wname}**  \n{format_price(wp)} ({wc:+.2f}%)")
        else:
            with c1: st.markdown(f"⚪ **{wname}**")
        with c2:
            if st.button("✕", key=f"del_{wt}"): to_remove = wt
    if to_remove:
        st.session_state.watchlist.remove(to_remove)
        st.rerun()

    st.markdown("---")
    st.caption("관심 종목 추가")
    wq = st.text_input("검색", placeholder="삼성전자, 005930", key="wq")
    if wq:
        wqr = {n: t for n, t in KOSPI_STOCKS.items() if wq.upper() in n.upper() or wq in t.replace(".KS","")}
        if wqr:
            wpick = st.selectbox("선택", list(wqr.keys()), key="wpick",
                                 format_func=lambda x: f"{x} ({wqr[x].replace('.KS','')})")
            if st.button("관심 추가", use_container_width=True):
                wt = wqr.get(wpick)
                if wt and wt not in st.session_state.watchlist:
                    st.session_state.watchlist.append(wt)
                    st.rerun()

# ── 메인 ────────────────────────────────────────────────
ticker_input = st.session_state.selected_ticker
display_name = TICKER_NAME_MAP.get(ticker_input, ticker_input.replace(".KS",""))
code_display = ticker_input.replace(".KS","")

st.markdown(f"## 📈 {display_name} ({code_display})")

with st.spinner("데이터 불러오는 중..."):
    info = get_stock_info(ticker_input)

if info is None:
    st.error(f"**{display_name}** 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")
    st.stop()

price   = info.get("currentPrice") or info.get("regularMarketPrice", 0)
chg_pct = info.get("regularMarketChangePercent", 0)
mkt_cap = info.get("marketCap", 0)
volume  = info.get("regularMarketVolume", 0)
high_52 = info.get("fiftyTwoWeekHigh", 0)
low_52  = info.get("fiftyTwoWeekLow", 0)
pe      = info.get("trailingPE", 0)
name    = info.get("longName") or info.get("shortName", display_name)

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("현재가",  format_price(price), f"{chg_pct:+.2f}%")
c2.metric("시가총액", format_cap(mkt_cap))
c3.metric("거래량",  f"{volume/1e4:.0f}만주" if volume else "N/A")
c4.metric("52주 최고", format_price(high_52) if high_52 else "N/A")
c5.metric("52주 최저", format_price(low_52)  if low_52  else "N/A")
c6.metric("P/E 비율",  f"{pe:.1f}" if pe else "N/A")

st.markdown("---")
col_chart, col_port = st.columns([2, 1])

# ── 차트 ────────────────────────────────────────────────
with col_chart:
    # 기간 버튼
    period_map = {"일": "3mo", "주": "1y", "월": "5y", "년": "10y"}
    pcols = st.columns(len(period_map))
    for i, (label, _) in enumerate(period_map.items()):
        with pcols[i]:
            btn_type = "primary" if st.session_state.chart_period == label else "secondary"
            if st.button(label, key=f"period_{label}", use_container_width=True, type=btn_type):
                st.session_state.chart_period = label
                st.rerun()
    plabel = st.session_state.chart_period
    if plabel not in period_map:
        st.session_state.chart_period = "일"
        plabel = "일"

    # 기간별 이동평균선 설정
    # 일봉: 5·20·60·120일
    # 주봉: 5·20·60·120주 → 실제 일수로 환산해서 동일 컬럼 사용
    # 월봉·년봉도 동일 컬럼(5·20·60·120) 사용 — 데이터 포인트 기준
    MA_SETTINGS = {
        "일": [
            ("MA5",   5,   "#FF6B35", 1.2, "MA5(5일)"),
            ("MA20",  20,  "#F5C518", 1.2, "MA20(20일)"),
            ("MA60",  60,  "#C084FC", 1.2, "MA60(60일)"),
            ("MA120", 120, "#FFFFFF", 1.5, "MA120(120일)"),
        ],
        "주": [
            ("MA5",   5,   "#FF6B35", 1.2, "MA5(5주)"),
            ("MA20",  20,  "#F5C518", 1.2, "MA20(20주)"),
            ("MA60",  60,  "#C084FC", 1.2, "MA60(60주)"),
            ("MA120", 120, "#FFFFFF", 1.5, "MA120(120주)"),
        ],
        "월": [
            ("MA5",   5,   "#FF6B35", 1.2, "MA5(5개월)"),
            ("MA20",  20,  "#F5C518", 1.2, "MA20(20개월)"),
            ("MA60",  60,  "#C084FC", 1.2, "MA60(60개월)"),
            ("MA120", 120, "#FFFFFF", 1.5, "MA120(120개월)"),
        ],
        "년": [
            ("MA5",   5,   "#FF6B35", 1.2, "MA5(5년)"),
            ("MA20",  20,  "#F5C518", 1.2, "MA20(20년)"),
            ("MA60",  60,  "#C084FC", 1.2, "MA60(60년)"),
            ("MA120", 120, "#FFFFFF", 1.5, "MA120(120년)"),
        ],
    }

    # 옵션 체크박스
    opt1, opt2, opt3 = st.columns(3)
    with opt1: show_ma = st.checkbox("이동평균선 (5·20·60·120)", value=True)
    with opt2: show_vp = st.checkbox("매물대 15구간", value=True)
    with opt3: draw_mode = st.selectbox("그리기 도구", ["없음","추세선","수평선"], label_visibility="collapsed")

    # 그리기 도구 UI
    if draw_mode == "추세선":
        st.caption("📏 추세선 — 시작/끝 날짜와 가격을 입력하세요")
        d1,d2,d3,d4,d5 = st.columns([2,2,2,2,1])
        line_x0 = d1.date_input("시작일", key="lx0")
        line_y0 = d2.number_input("시작가", min_value=0, value=int(price) if price else 0, step=100, key="ly0")
        line_x1 = d3.date_input("끝날짜", key="lx1")
        line_y1 = d4.number_input("끝가격", min_value=0, value=int(price) if price else 0, step=100, key="ly1")
        with d5:
            st.markdown("<div style='margin-top:26px'>", unsafe_allow_html=True)
            if st.button("추가", key="add_trend"):
                st.session_state.drawn_lines.append({
                    "type":"trend","x0":str(line_x0),"y0":line_y0,
                    "x1":str(line_x1),"y1":line_y1,"color":"#F5A623"
                })
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    elif draw_mode == "수평선":
        st.caption("📐 수평선 — 가격을 입력하세요")
        h1, h2 = st.columns([5,1])
        h_price = h1.number_input("가격", min_value=0, value=int(price) if price else 0, step=100, key="hprice")
        with h2:
            st.markdown("<div style='margin-top:26px'>", unsafe_allow_html=True)
            if st.button("추가", key="add_hline"):
                st.session_state.drawn_lines.append({"type":"hline","y":h_price,"color":"#A78BFA"})
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.drawn_lines:
        if st.button(f"선 전체 삭제 ({len(st.session_state.drawn_lines)}개)", key="clear_lines"):
            st.session_state.drawn_lines = []
            st.rerun()

    hist_raw = get_history(ticker_input, period_map[plabel])

    if not hist_raw.empty:
        hist = hist_raw.copy()

        # 주봉·월봉·년봉 리샘플링
        if plabel == "주":
            hist = hist.resample("W").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna()
        elif plabel == "월":
            hist = hist.resample("ME").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna()
        elif plabel == "년":
            hist = hist.resample("YE").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna()

        # 이동평균선 계산 (데이터 포인트 기준)
        ma_cfg = MA_SETTINGS.get(plabel, MA_SETTINGS["일"])
        for col, window, _, _, _ in ma_cfg:
            hist[col] = hist["Close"].rolling(window).mean()

        # 매물대 계산
        NUM_VP = 15
        p_min = hist["Low"].min()
        p_max = hist["High"].max()
        p_range = p_max - p_min
        bin_size = p_range / NUM_VP
        vp_data = []
        for i in range(NUM_VP):
            lo = p_min + i * bin_size
            hi = lo + bin_size
            mid = (lo + hi) / 2
            vol = hist[(hist["Close"] >= lo) & (hist["Close"] < hi)]["Volume"].sum()
            vp_data.append({"lo": lo, "hi": hi, "mid": mid, "vol": vol})
        vp_df = pd.DataFrame(vp_data)
        vp_max = vp_df["vol"].max() if vp_df["vol"].max() > 0 else 1

        # 날짜 범위
        x_end   = hist.index[-1]
        x_start = hist.index[0]
        total_days = max((x_end - x_start).days, 1)
        # 매물대 최대 너비: 전체 기간의 15% — 오른쪽→왼쪽이므로 음수 방향
        vp_max_width_days = int(total_days * 0.15)

        up_color   = "#3182F6"
        down_color = "#F04452"

        fig = go.Figure()

        # 캔들스틱
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist["Open"], high=hist["High"],
            low=hist["Low"],  close=hist["Close"],
            name="캔들",
            increasing=dict(line=dict(color=up_color,   width=1), fillcolor=up_color),
            decreasing=dict(line=dict(color=down_color, width=1), fillcolor=down_color),
            whiskerwidth=0.5,
            hovertext=[
                f"시가 {format_price(o)}<br>고가 {format_price(h)}<br>저가 {format_price(l)}<br>종가 {format_price(c)}"
                for o,h,l,c in zip(hist["Open"],hist["High"],hist["Low"],hist["Close"])
            ],
            hoverinfo="text+x",
        ))

        # 이동평균선
        if show_ma:
            for col, _, color, width, label in ma_cfg:
                valid = hist[col].dropna()
                if not valid.empty:
                    fig.add_trace(go.Scatter(
                        x=hist.index, y=hist[col], mode="lines",
                        line=dict(color=color, width=width), name=label,
                        hovertemplate=f"{label}: ₩%{{y:,.0f}}<extra></extra>"
                    ))

        # 매물대 — x_end 기준으로 왼쪽(-) 방향으로 그리기
        if show_vp:
            current_close = hist["Close"].iloc[-1]
            for _, row in vp_df.iterrows():
                if row["vol"] == 0:
                    continue
                bar_days = max(int(vp_max_width_days * row["vol"] / vp_max), 1)
                # 오른쪽(x_end)에서 왼쪽으로 뻗도록 x0 > x1
                bar_start = x_end
                bar_end_x = x_end - pd.Timedelta(days=bar_days)
                is_above = row["mid"] >= current_close
                fill = "rgba(49,130,246,0.50)" if is_above else "rgba(49,130,246,0.22)"
                fig.add_shape(
                    type="rect",
                    x0=bar_end_x, x1=bar_start,
                    y0=row["lo"],  y1=row["hi"],
                    fillcolor=fill, line=dict(width=0),
                    xref="x", yref="y", layer="above"
                )
            # 현재가 점선
            fig.add_hline(
                y=current_close,
                line=dict(color=up_color, width=1, dash="dot"),
                annotation_text=f" {format_price(current_close)}",
                annotation_position="right",
                annotation_font=dict(size=11, color=up_color)
            )

        # 사용자가 그린 선
        for ln in st.session_state.drawn_lines:
            if ln["type"] == "trend":
                fig.add_shape(
                    type="line",
                    x0=ln["x0"], y0=ln["y0"],
                    x1=ln["x1"], y1=ln["y1"],
                    line=dict(color=ln["color"], width=1.5),
                    xref="x", yref="y"
                )
                fig.add_annotation(
                    x=ln["x1"], y=ln["y1"],
                    text=f"  {format_price(ln['y1'])}",
                    showarrow=False, font=dict(size=10, color=ln["color"]),
                    xref="x", yref="y"
                )
            elif ln["type"] == "hline":
                fig.add_hline(
                    y=ln["y"],
                    line=dict(color=ln["color"], width=1.5, dash="dash"),
                    annotation_text=f" {format_price(ln['y'])}",
                    annotation_position="right",
                    annotation_font=dict(size=10, color=ln["color"])
                )

        tick_fmt_map = {"일": "%m.%d", "주": "%y.%m.%d", "월": "%y.%m", "년": "%Y"}
        tick_fmt = tick_fmt_map.get(plabel, "%m.%d")
        fig.update_layout(
            height=500,
            margin=dict(l=0, r=90, t=10, b=0),
            plot_bgcolor="#0E1117",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                showgrid=False, zeroline=False, showline=False,
                tickfont=dict(size=11, color="#666"),
                tickformat=tick_fmt,
                rangeslider=dict(visible=False),
            ),
            yaxis=dict(
                showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                zeroline=False, showline=False,
                tickfont=dict(size=11, color="#666"),
                tickformat=",", side="right",
            ),
            hovermode="x unified",
            legend=dict(
                orientation="h", y=1.02, x=0,
                font=dict(size=11, color="#aaa"),
                bgcolor="rgba(0,0,0,0)",
            ),
            dragmode="zoom",
        )
        st.plotly_chart(fig, use_container_width=True, config={
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["lasso2d","select2d","autoScale2d"],
            "displaylogo": False,
            "scrollZoom": True,
        })

        # 거래량 차트
        vol_colors = [up_color if c >= o else down_color
                      for c, o in zip(hist["Close"], hist["Open"])]
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Bar(
            x=hist.index, y=hist["Volume"],
            marker_color=vol_colors,
            hovertemplate="<b>%{x|%Y.%m.%d}</b><br>%{y:,.0f}주<extra></extra>",
        ))
        fig_vol.update_layout(
            height=90, margin=dict(l=0, r=90, t=0, b=0),
            plot_bgcolor="#0E1117", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, side="right"),
            showlegend=False, bargap=0.15,
        )
        st.plotly_chart(fig_vol, use_container_width=True, config={"displayModeBar": False})

        # 범례 안내
        st.markdown(
            "<span style='font-size:11px;color:#555;'>"
            "거래량 &nbsp;|&nbsp; "
            "<span style='color:#FF6B35'>■ MA5</span> &nbsp;"
            "<span style='color:#F5C518'>■ MA20</span> &nbsp;"
            "<span style='color:#C084FC'>■ MA60</span> &nbsp;"
            "<span style='color:#FFFFFF'>■ MA120</span> &nbsp;|&nbsp; "
            "<span style='color:#F5A623'>— 추세선</span> &nbsp;"
            "<span style='color:#A78BFA'>-- 수평선</span>"
            "</span>",
            unsafe_allow_html=True
        )
    else:
        st.info("차트 데이터를 불러올 수 없습니다.")

# ── 포트폴리오 ──────────────────────────────────────────
with col_port:
    st.markdown("### 💼 포트폴리오")
    with st.form("add_portfolio"):
        pa,pb,pc = st.columns([2,1,1])
        p_ticker = pa.text_input("종목코드 (6자리)", value=code_display)
        p_shares = pb.number_input("수량", min_value=1, value=10)
        p_price  = pc.number_input("매수가", min_value=1.0, value=float(price) if price else 1000.0, step=100.0)
        if st.form_submit_button("추가", use_container_width=True):
            code = p_ticker.strip().zfill(6) + ".KS"
            st.session_state.portfolio.append({"ticker": code, "shares": p_shares, "avg_price": p_price})
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
            total_invest += inv; total_value += val
            pname = TICKER_NAME_MAP.get(item["ticker"], item["ticker"].replace(".KS",""))
            rows.append({"종목": pname, "수량": item["shares"],
                         "매수가": format_price(item["avg_price"]),
                         "현재가": format_price(cp),
                         "손익": f"₩{pnl:+,.0f} ({pnl_pct:+.1f}%)"})
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
col_news, col_ai = st.columns([1,1])

# ── 뉴스 ────────────────────────────────────────────────
with col_news:
    st.markdown("### 📰 관련 뉴스")
    news = get_news(ticker_input)
    if news:
        for item in news:
            title    = item.get("title","")
            link     = item.get("link","#")
            pub      = item.get("publisher","")
            pt       = item.get("providerPublishTime",0)
            ts       = datetime.fromtimestamp(pt).strftime("%m/%d %H:%M") if pt else ""
            st.markdown(f"**[{title}]({link})**  \n_{pub} · {ts}_")
            st.markdown("---")
    else:
        st.info("뉴스를 불러올 수 없습니다.")

# ── AI 분석 ─────────────────────────────────────────────
with col_ai:
    st.markdown("### 🤖 AI 주식 분석 (Gemini)")
    try:
        api_key = st.secrets.get("GEMINI_API_KEY","")
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
                f"{TICKER_NAME_MAP.get(p['ticker'],p['ticker'].replace('.KS',''))} {p['shares']}주"
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
                    response = model.generate_content(f"주식 데이터:\n{stock_summary}\n\n질문: {question}")
                    st.success(response.text)
                except Exception as e:
                    st.error(f"오류 발생: {e}")
