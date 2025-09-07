# 🎯 YouTube Analytics Pro

<div align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/YouTube_API-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="YouTube API">
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5">
  <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3">
</div>

<br>

> **🚀 프로페셔널 YouTube 채널 분석 및 수익성 평가 도구**  
> YouTube Data API v3를 활용한 채널 데이터 분석, 동영상 성과 추적, 수익 예측 웹 애플리케이션

## 📋 목차

- [🎯 프로젝트 소개](#-프로젝트-소개)
- [✨ 주요 기능](#-주요-기능)
- [🛠️ 기술 스택](#️-기술-스택)
- [⚡ 빠른 시작](#-빠른-시작)
- [📊 기능 상세 설명](#-기능-상세-설명)
- [🎨 UI/UX 특징](#-uiux-특징)
- [📁 프로젝트 구조](#-프로젝트-구조)
- [🔧 설정 방법](#-설정-방법)
- [💡 사용 예시](#-사용-예시)
- [🤝 기여하기](#-기여하기)
- [📄 라이센스](#-라이센스)

---

## 🎯 프로젝트 소개

**YouTube Analytics Pro**는 YouTube 채널 운영자와 콘텐츠 크리에이터를 위한 종합적인 분석 도구입니다. YouTube Data API v3를 활용하여 채널의 성과를 실시간으로 분석하고, 수익성을 예측하여 비즈니스 의사결정을 지원합니다.

### 🎯 프로젝트 목적
- YouTube 채널의 데이터 기반 성과 분석
- 수익 창출 가능성 평가 및 예측
- 콘텐츠 전략 수립을 위한 인사이트 제공
- 사용자 친화적인 웹 인터페이스 제공

---

## ✨ 주요 기능

### 📺 **채널 종합 정보**
- 구독자 수, 총 조회수, 동영상 개수 실시간 조회
- 채널 기본 정보 및 설명 표시
- 채널 성장률 및 참여도 분석

### 📊 **동영상 성과 분석**
- 최신/인기 동영상 TOP 5 자동 선별
- 평균 조회수 및 참여율 계산
- 동영상별 상세 통계 (조회수, 좋아요, 댓글 수)
- 썸네일 이미지와 함께 시각적 표시

### 💰 **수익 예측 시스템**
- **광고 수익**: CPM 기반 월간 수익 예측
- **스폰서십**: 구독자 기반 협찬 수익 계산
- **멤버십**: 채널 멤버십 수익 추정
- **연간 수익**: 통합 수익 연간 예측

### 🔍 **고급 검색 기능**
- 채널명 또는 YouTube URL 입력 지원
- URL 자동 파싱 및 채널 ID 추출
- 다양한 YouTube URL 형식 호환

### 📋 **전체 동영상 목록**
- 사용자 지정 개수만큼 동영상 분석
- 페이지네이션으로 효율적인 데이터 탐색
- 동영상별 클릭 가능한 직접 링크

### 🌙 **다크 모드**
- 라이트/다크 테마 토글
- 사용자 설정 자동 저장
- 눈의 피로감 최소화

---

## 🛠️ 기술 스택

### **백엔드**
- **Python 3.8+** - 메인 개발 언어
- **Flask** - 경량 웹 프레임워크
- **YouTube Data API v3** - 데이터 수집
- **JSON** - 데이터 교환 포맷

### **프론트엔드**
- **HTML5** - 마크업 구조
- **CSS3** - 스타일링 및 반응형 디자인
- **JavaScript (ES6+)** - 동적 상호작용
- **Google Fonts (Inter)** - 타이포그래피

### **디자인 시스템**
- **CSS Variables** - 테마 시스템
- **Flexbox & Grid** - 레이아웃
- **CSS Animations** - 부드러운 전환 효과
- **Responsive Design** - 모바일 최적화

---

## ⚡ 빠른 시작

### 1️⃣ **저장소 클론**
```bash
git clone https://github.com/araeLaver/YouTube_Analytics-.git
cd YouTube_Analytics-
```

### 2️⃣ **의존성 설치**
```bash
pip install flask google-api-python-client
```

### 3️⃣ **YouTube API 키 설정**
1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. YouTube Data API v3 활성화
3. API 키 생성
4. `working_analyzer.py` 파일의 `API_KEY` 변수에 키 입력

### 4️⃣ **애플리케이션 실행**
```bash
python working_analyzer.py
```

### 5️⃣ **웹 브라우저에서 접속**
```
http://localhost:8080
```

---

## 📊 기능 상세 설명

### 🔍 **채널 분석 프로세스**

1. **채널 검색**: 채널명 또는 URL 입력
   ```python
   # 지원되는 URL 형식
   - https://youtube.com/@채널명
   - https://youtube.com/c/채널명
   - https://youtube.com/channel/채널ID
   - https://youtube.com/user/사용자명
   ```

2. **데이터 수집**: YouTube API를 통한 실시간 데이터 획득
   ```python
   # 수집되는 데이터
   - 채널 기본 정보 (이름, 설명, 구독자 수)
   - 동영상 목록 (제목, 조회수, 좋아요, 댓글 수)
   - 업로드 날짜 및 썸네일 이미지
   ```

3. **분석 및 계산**: 다양한 지표 계산
   ```python
   # 계산되는 지표
   - 평균 조회수 = 총 조회수 / 동영상 수
   - 참여율 = (좋아요 수 / 조회수) * 100
   - CPM 기반 광고 수익 예측
   ```

### 💰 **수익 계산 알고리즘**

#### 📺 광고 수익
```python
월간_광고수익 = (평균_조회수 × 8 / 1000) × 3000원
# - 8회: 월간 업로드 횟수 (주 2회)
# - CPM: 1000회당 3000원 (한국 평균)
```

#### 🤝 스폰서십 수익
```python
월간_스폰서십 = 구독자수 × 50원 / 12개월
# - 구독자 10,000명 이상 시 적용
# - 연간 구독자당 50원 기준
```

#### 👥 멤버십 수익
```python
월간_멤버십 = 구독자수 × 0.015 × 4900원
# - 구독자 1,000명 이상 시 적용
# - 1.5% 멤버십 가입률
# - 월 4,900원 멤버십 기준
```

---

## 🎨 UI/UX 특징

### 🎯 **사용자 중심 디자인**
- **직관적 네비게이션**: 명확한 정보 계층구조
- **반응형 디자인**: 모바일, 태블릿, 데스크톱 최적화
- **접근성**: 고대비 색상 및 읽기 쉬운 폰트

### 🎨 **모던 비주얼 시스템**
- **그라디언트 효과**: 브랜드 정체성 강화
- **카드 기반 레이아웃**: 정보의 논리적 그룹화
- **마이크로 애니메이션**: 사용자 피드백 향상

### 🌈 **컬러 시스템**
```css
/* 라이트 테마 */
--bg-primary: #f8fafc;
--text-primary: #1e293b;
--gradient-brand: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* 다크 테마 */
--bg-primary: #0f172a;
--text-primary: #f8fafc;
```

---

## 📁 프로젝트 구조

```
YouTube_Analytics/
├── working_analyzer.py     # 메인 애플리케이션
├── quick_test.py          # API 연결 테스트
├── fixed_analyzer.py      # 안정화 버전
├── modern_analyzer.py     # 모던 UI 버전
├── selective_analyzer.py  # 선택적 분석 버전
├── README.md             # 프로젝트 문서
└── .git/                 # Git 저장소
```

### 📄 **파일 설명**
- `working_analyzer.py`: 완성된 메인 애플리케이션
- `quick_test.py`: YouTube API 연결 상태 확인 도구
- `fixed_analyzer.py`: 버그 수정된 안정 버전
- `modern_analyzer.py`: UI/UX 개선 버전
- `selective_analyzer.py`: 고급 필터링 기능 포함

---

## 🔧 설정 방법

### 🔑 **YouTube API 키 발급**

1. **Google Cloud Console 접속**
   - https://console.cloud.google.com/ 방문
   - Google 계정으로 로그인

2. **새 프로젝트 생성**
   ```
   프로젝트 이름: YouTube Analytics
   ```

3. **YouTube Data API v3 활성화**
   ```
   API 및 서비스 > 라이브러리 > YouTube Data API v3 검색 > 사용
   ```

4. **API 키 생성**
   ```
   사용자 인증 정보 > 사용자 인증 정보 만들기 > API 키
   ```

5. **API 키 제한 설정** (선택사항)
   ```
   HTTP 리퍼러: http://localhost:8080/*
   API 제한: YouTube Data API v3
   ```

### ⚙️ **환경 설정**

```python
# working_analyzer.py 파일 수정
API_KEY = "YOUR_YOUTUBE_API_KEY_HERE"
```

---

## 💡 사용 예시

### 🎬 **채널 분석 시나리오**

#### 1️⃣ 인기 채널 분석
```
입력: "로직알려주는남자"
결과: 구독자 20.2만명, 월 예상 수익 230만원
```

#### 2️⃣ URL을 통한 분석
```
입력: "https://www.youtube.com/@보다BODA"
결과: 자동 URL 파싱 후 채널 분석
```

#### 3️⃣ 대용량 데이터 분석
```
설정: 분석할 동영상 수 300개
결과: 상세한 통계 및 트렌드 분석
```

---

## 🤝 기여하기

### 🐛 **버그 리포트**
[Issues](https://github.com/araeLaver/YouTube_Analytics-/issues)에서 버그를 신고해주세요.

### 💡 **기능 제안**
새로운 기능 아이디어는 [Discussions](https://github.com/araeLaver/YouTube_Analytics-/discussions)에서 제안해주세요.

### 🔧 **개발 기여**
1. Fork 프로젝트
2. Feature 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push (`git push origin feature/AmazingFeature`)
5. Pull Request 생성

---

## 🚀 로드맵

### 🎯 **v2.0 계획**
- [ ] 다중 채널 비교 분석
- [ ] 수익 예측 AI 모델 도입
- [ ] Excel/PDF 리포트 내보내기
- [ ] 실시간 알림 시스템

### 🎯 **v3.0 계획**
- [ ] 소셜 미디어 통합 분석
- [ ] 경쟁사 벤치마킹 기능
- [ ] API 서비스화
- [ ] 모바일 앱 개발

---

## 📞 연락처

- **개발자**: [araeLaver](https://github.com/araeLaver)
- **프로젝트 링크**: [https://github.com/araeLaver/YouTube_Analytics-](https://github.com/araeLaver/YouTube_Analytics-)

---

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

---

<div align="center">
  <h3>🌟 이 프로젝트가 도움이 되었다면 Star를 눌러주세요! 🌟</h3>
  
  **Made with ❤️ by araeLaver**
</div>