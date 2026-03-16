# 📈 주식 대시보드 (Streamlit)

yfinance + Claude API 기반 주식 분석 대시보드

## 기능
- 실시간 주가 조회 (Yahoo Finance)
- 캔들스틱 차트 (1주 ~ 5년)
- 포트폴리오 관리 & 손익 계산
- 관심 종목 위젯
- 관련 뉴스 피드
- Claude AI 주식 분석
- 로그인 화면 (비밀번호 보호)

---

## 로컬 실행

### 1. 설치
```bash
pip install -r requirements.txt
```

### 2. 시크릿 설정
```bash
mkdir .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# secrets.toml 파일을 열어 비밀번호와 API 키 입력
```

### 3. 실행
```bash
streamlit run app.py
```

브라우저에서 http://localhost:8501 접속

---

## Streamlit Cloud 무료 배포

### 1. GitHub에 올리기
```bash
git init
git add .
git commit -m "주식 대시보드"
git remote add origin https://github.com/YOUR_ID/stock-dashboard.git
git push -u origin main
```

> ⚠️ `.streamlit/secrets.toml`은 `.gitignore`에 추가해서 GitHub에 올리지 마세요!

### 2. Streamlit Cloud 연결
1. https://share.streamlit.io 접속
2. GitHub 계정 연결
3. 저장소 선택 → `app.py` 선택
4. **Advanced settings → Secrets** 에 아래 내용 입력:
   ```
   USERNAME = "admin"
   PASSWORD = "your_password"
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
5. Deploy 클릭 → 약 1분 후 URL 생성

---

## 한국 주식 사용법
한국 주식은 종목 코드 뒤에 `.KS` 를 붙이세요:
- 삼성전자: `005930.KS`
- SK하이닉스: `000660.KS`
- 카카오: `035720.KS`

---

## 파일 구조
```
stock_dashboard/
├── app.py                        # 메인 앱
├── requirements.txt              # 패키지 목록
└── .streamlit/
    └── secrets.toml.example      # 시크릿 설정 예시
```
