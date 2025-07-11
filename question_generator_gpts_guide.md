# 질문 생성기 GPTS 개발 지침서 (for CURSOR AI)

## 1. 💡 프로젝트 개요
- **앱 이름:** 질문연금술사
- **목표 및 목적:** 
  - 사용자가 입력한 콘텐츠(PDF, 텍스트, 유튜브, 웹사이트)를 요약 및 주제 추출하여
  - 분석/종합/평가 수준의 고차원 질문을 생성하고,
  - 사용자 질문 인식 능력을 객관식으로 진단,
  - GPT 피드백을 통해 질문 능력 향상을 지원

- **사용자 시나리오:**  
  1. 콘텐츠 입력  
  2. 요약 및 핵심 주제 추출  
  3. 고차원 질문 생성  
  4. 객관식 평가 및 채점  
  5. GPT 피드백  
  6. 진단 요약 및 학습 전략 제안

---

## 2. 🔧 주요 기능 요약

### 기능 1: 콘텐츠 입력 처리
- **입력값:** 텍스트, PDF, 유튜브 URL, 웹사이트 URL
- **출력값:** 콘텐츠 원문
- **기술:** pdf-parse, Cheerio, YouTube API

### 기능 2: 요약 및 핵심 주제 추출
- **입력값:** 콘텐츠 원문
- **출력값:** 요약문, 핵심 키워드
- **API:** GPT API

### 기능 3: 고차원 질문 생성
- **입력값:** 요약문 + 주제
- **출력값:** 질문(수준, 이유 포함)
- **API:** GPT + Bloom’s 기준

### 기능 4: 객관식 질문 수준 평가
- **입력값:** 질문 + GPT 수준
- **출력값:** 객관식 보기
- **목적:** 사용자 인식 진단

### 기능 5: GPT 피드백
- **입력값:** 사용자 선택 vs GPT 정답
- **출력값:** 피드백 문장
- **포인트:** 따뜻하고 구체적인 설명

### 기능 6: 결과 저장 및 분석
- **출력:** GPT 응답, 사용자 반응 기록, 통계 시각화

---

## 3. 🧱 개발 순서 제안

1. 프로젝트 구조 생성 (Next.js + Tailwind)
2. 콘텐츠 입력 UI 구현
3. GPT 요약/주제 추출 연동
4. 질문 생성 프롬프트 연결
5. 객관식 보기 자동 생성 및 사용자 입력 처리
6. GPT 피드백 출력 구현
7. 전체 결과 저장 및 통계 분석
8. 배포 (Vercel)

---

## 4. ⚙️ 개발 환경 정보

- 플랫폼: Next.js (웹)
- 운영체제: Windows / macOS
- 도구: Cursor AI, VSCode
- 언어: TypeScript / JavaScript
- 외부 API: GPT, YouTube, Google Sheets (선택)

---

## 5. 🧠 전체 프롬프트 흐름

### 프롬프트 1: 콘텐츠 요약 및 핵심 주제

```
다음 콘텐츠를 요약하고 핵심 주제를 추출해줘:

"""
{{콘텐츠 원문}}
"""

[요약]
{{요약문}}

[핵심 주제]
- 주제1
- 주제2 ...
```

---

### 프롬프트 2: 고차원 질문 생성

```
[요약문]
{{요약문}}

[핵심 주제]
- {{주제1}}, {{주제2}}, ...

분석/종합/평가 수준 질문을 총 3~5개 생성해줘.  
각 질문에는 수준과 이유도 포함:

[
  {
    "질문": "...",
    "수준": "...",
    "이유": "..."
  }
]
```

---

### 프롬프트 3: 객관식 평가 생성

```
[질문] "..."

이 질문의 사고 수준은?

A. 기억  
B. 이해  
C. 적용  
D. 분석  
E. 평가 ✅
```

---

### 프롬프트 4: 사용자 피드백 생성

```
[질문]: "...",  
[GPT 판단 수준]: "평가",  
[사용자 선택 수준]: "이해"

이 차이를 바탕으로 친절하고 교육적인 피드백을 작성해줘.
```

---

### 프롬프트 5: 진단 요약

```
사용자 객관식 응답 결과:

- 질문 1: 평가 / 이해 ❌
- 질문 2: 분석 / 분석 ✅
- 질문 3: 종합 / 적용 ❌

전체 정확도, 오답 경향, 학습 전략 3가지를 제안해줘.
```

---

## 📎 사용 시 참고

- 각 프롬프트는 Cursor 카드로 등록 가능  
- 단독 API 호출 또는 연결형 흐름 처리도 가능  
- 질문 생성기 앱, 평가 앱, 튜터형 앱으로 확장 가능
