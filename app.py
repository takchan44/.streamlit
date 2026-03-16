import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import anthropic

st.set_page_config(
    page_title="주식 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 세션 초기화 ─────────────────────────────────────────
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["AAPL", "MSFT", "NVDA", "GOOGL", "TSLA"]

# ── 주식 데이터 가져오기 ────────────────────────────────
@st.cache_data(ttl=60)
def get_stock_info(ticker: str):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        hist = t.history(period="1d", interval="1m")
        return info, hist
    except Exception:
        return None, None

@st.cache_data(ttl=300)
def get_history(ticker: str, period: str):
    try:
        t = yf.Ticker(ticker)
        return t.history(period=period)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_news(ticker: str):
    try:
        t = yf.Ticker(ticker)
        return t.news[:5] if t.news else []
    except Exception:
        return []

# ── 사이드바 ────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 종목 조회")
    ticker_input = st.text_input("종목 코드", value="AAPL", placeholder="AAPL, MSFT, 005930.KS")
    ticker_input = ticker_input.upper().strip()

    st.markdown("---")
    st.markdown("### ⭐ 관심 종목")
    for wt in st.session_state.watchlist:
        info, _ = get_stock_info(wt)
        if info:
            price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
            chg = info.get("regularMarketChangePercent", 0)
            color = "🟢" if chg >= 0 else "🔴"
            st.markdown(f"{color} **{wt}** ${price:,.2f} ({chg:+.2f}%)")

    st.markdown("---")
    new_watch = st.text_input("관심 종목 추가", placeholder="AMZN")
    if st.button("추가", use_container_width=True) and new_watch:
        wt = new_watch.upper().strip()
        if wt not in st.session_state.watchlist:
            st.session_state.watchlist.append(wt)
            st.rerun()

# ── 메인 화면 ───────────────────────────────────────────
st.markdown("## 📈 주식 대시보드")

info, hist_1d = get_stock_info(ticker_input)

if info is None:
    st.error(f"'{ticker_input}' 종목 정보를 불러올 수 없습니다.")
    st.stop()

# 지표 카드
price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
change = info.get("regularMarketChange", 0)
change_pct = info.get("regularMarketChangePercent", 0)
mkt_cap = info.get("marketCap", 0)
volume = info.get("regularMarketVolume", 0)
high_52 = info.get("fiftyTwoWeekHigh", 0)
low_52 = info.get("fiftyTwoWeekLow", 0)
pe = info.get("trailingPE", 0)
name = info.get("longName", ticker_input)

c1, c2, c3, c4, c5, c6 = st.columns(6)
delta_color = "normal"
c1.metric("현재가", f"${price:,.2f}", f"{change:+.2f} ({change_pct:+.2f}%)", delta_color=delta_color)
c2.metric("시가총액", f"${mkt_cap/1e9:.1f}B" if mkt_cap else "N/A")
c3.metric("거래량", f"{volume/1e6:.1f}M" if volume else "N/A")
c4.metric("52주 최고", f"${high_52:,.2f}" if high_52 else "N/A")
c5.metric("52주 최저", f"${low_52:,.2f}" if low_52 else "N/A")
c6.metric("P/E 비율", f"{pe:.1f}" if pe else "N/A")

st.markdown("---")

# 차트 + 포트폴리오
col_chart, col_port = st.columns([2, 1])

with col_chart:
    st.markdown(f"### {name} ({ticker_input}) 주가 차트")
    period_map = {"1주": "5d", "1달": "1mo", "3달": "3mo", "6달": "6mo", "1년": "1y", "5년": "5y"}
    period_label = st.radio("기간", list(period_map.keys()), horizontal=True, index=2)
    hist = get_history(ticker_input, period_map[period_label])

    if not hist.empty:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist["Open"],
            high=hist["High"],
            low=hist["Low"],
            close=hist["Close"],
            name=ticker_input,
            increasing_line_color="#1D9E75",
            decreasing_line_color="#E24B4A"
        ))
        fig.add_trace(go.Bar(
            x=hist.index,
            y=hist["Volume"],
            name="거래량",
            yaxis="y2",
            marker_color="rgba(100,130,200,0.3)"
        ))
        fig.update_layout(
            yaxis2=dict(overlaying="y", side="right", showgrid=False, title="거래량"),
            xaxis_rangeslider_visible=False,
            height=400,
            margin=dict(l=0, r=0, t=20, b=0),
            legend=dict(orientation="h", y=1.05)
        )
        st.plotly_chart(fig, use_container_width=True)

with col_port:
    st.markdown("### 💼 포트폴리오")
    with st.form("add_portfolio"):
        pa, pb, pc = st.columns([2, 1, 1])
        p_ticker = pa.text_input("종목", placeholder="AAPL")
        p_shares = pb.number_input("수량", min_value=1, value=10)
        p_price = pc.number_input("매수가", min_value=0.01, value=100.0)
        if st.form_submit_button("추가", use_container_width=True):
            st.session_state.portfolio.append({
                "ticker": p_ticker.upper().strip(),
                "shares": p_shares,
                "avg_price": p_price
            })
            st.rerun()

    if st.session_state.portfolio:
        total_invest = 0
        total_value = 0
        rows = []
        for item in st.session_state.portfolio:
            cur_info, _ = get_stock_info(item["ticker"])
            cur_price = (cur_info.get("currentPrice") or cur_info.get("regularMarketPrice", item["avg_price"])) if cur_info else item["avg_price"]
            invest = item["avg_price"] * item["shares"]
            value = cur_price * item["shares"]
            pnl = value - invest
            pnl_pct = (pnl / invest) * 100
            total_invest += invest
            total_value += value
            rows.append({
                "종목": item["ticker"],
                "수량": item["shares"],
                "매수가": f"${item['avg_price']:.2f}",
                "현재가": f"${cur_price:.2f}",
                "평가손익": f"${pnl:+.0f} ({pnl_pct:+.1f}%)"
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, hide_index=True, use_container_width=True)
        total_pnl = total_value - total_invest
        total_pnl_pct = (total_pnl / total_invest) * 100 if total_invest else 0
        st.metric("총 평가손익", f"${total_pnl:+,.0f}", f"{total_pnl_pct:+.2f}%")
        if st.button("포트폴리오 초기화"):
            st.session_state.portfolio = []
            st.rerun()
    else:
        st.info("종목을 추가해보세요.")

st.markdown("---")

# 뉴스 + AI 분석
col_news, col_ai = st.columns([1, 1])

with col_news:
    st.markdown("### 📰 관련 뉴스")
    news = get_news(ticker_input)
    if news:
        for item in news:
            title = item.get("title", "")
            link = item.get("link", "#")
            publisher = item.get("publisher", "")
            pub_time = item.get("providerPublishTime", 0)
            time_str = datetime.fromtimestamp(pub_time).strftime("%m/%d %H:%M") if pub_time else ""
            st.markdown(f"**[{title}]({link})**  \n_{publisher} · {time_str}_")
            st.markdown("---")
    else:
        st.info("뉴스를 불러올 수 없습니다.")

with col_ai:
    st.markdown("### 🤖 AI 주식 분석")
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else ""
    question = st.text_area(
        "질문 입력",
        placeholder=f"예: {ticker_input} 지금 매수하기 좋은 타이밍인가요?",
        height=100
    )
    if st.button("AI 분석 요청 ↗", use_container_width=True):
        if not api_key:
            st.warning("`.streamlit/secrets.toml`에 `ANTHROPIC_API_KEY`를 설정해주세요.")
        elif not question.strip():
            st.warning("질문을 입력해주세요.")
        else:
            port_summary = ", ".join([f"{p['ticker']} {p['shares']}주" for p in st.session_state.portfolio]) or "없음"
            stock_summary = f"""
종목: {name} ({ticker_input})
현재가: ${price:,.2f}
등락률: {change_pct:+.2f}%
시가총액: ${mkt_cap/1e9:.1f}B
P/E: {pe:.1f}
52주 범위: ${low_52:,.2f} ~ ${high_52:,.2f}
포트폴리오: {port_summary}
            """.strip()
            with st.spinner("Claude가 분석 중..."):
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    message = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1024,
                        system="당신은 전문 주식 분석가입니다. 주어진 데이터를 바탕으로 명확하고 유익한 분석을 제공하세요. 항상 투자 위험을 언급하세요.",
                        messages=[{
                            "role": "user",
                            "content": f"주식 데이터:\n{stock_summary}\n\n질문: {question}"
                        }]
                    )
                    st.success(message.content[0].text)
                except Exception as e:
                    st.error(f"오류 발생: {e}")
