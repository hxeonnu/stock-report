# GPT 기반 주가·뉴스 자동 리포트 시스템

주가 및 관련 뉴스 데이터를 자동으로 수집하고, GPT를 활용해 분석한 리포트를 Slack으로 전송하는 자동화 프로젝트입니다.

## 주요 기능

- Yahoo Finance 기반 주가 및 거래량 데이터 수집
- Naver 뉴스 검색 결과 및 기사 본문 크롤링
- 환율 정보 수집 및 원화 환산
- OpenAI API를 활용한 주가·뉴스 데이터 분석 및 요약
- Slack Webhook을 통한 리포트 자동 전송
- 지정된 시간에 전체 프로세스 자동 실행

## System Flow

Data Collection  
→ Data Preprocessing  
→ GPT Analysis  
→ Report Generation  
→ Slack Notification

## Tech Stack

- Python 3.13
- Requests
- BeautifulSoup
- Playwright
- OpenAI API
- Slack Webhook
- Schedule
- JSON / Regular Expression

## Project Structure

```text
project/
├── stock/
│   └── stock_data_collection
├── news/
│   └── news_crawling
├── gpt/
│   └── report_generation
├── slack/
│   └── slack_notification
├── data/
│   └── json_data
└── main.py
```

※ 실제 프로젝트 디렉터리 구조에 맞게 수정

## 주요 개발 과정

### 1. 주가 데이터 수집

초기에는 네이버 금융을 대상으로 크롤링을 시도했으나 접근 제한과 페이지 구조 문제로 안정적인 수집이 어려웠습니다.

이후 Yahoo Finance로 데이터 수집 대상을 변경하여 주가 및 거래량 데이터를 수집했습니다.

### 2. 뉴스 크롤링 안정화

뉴스 검색 결과의 CSS 선택자가 변경되면서 크롤링이 불안정해지는 문제가 발생했습니다.

DOM 구조를 분석하여 비교적 일정하게 유지되는 요소를 기준으로 기사 제목과 URL을 추출하도록 수집 방식을 개선했습니다.

### 3. 동적 페이지 처리

일부 뉴스 본문은 동적으로 렌더링되어 Requests만으로 수집할 수 없었습니다.

Selenium을 먼저 적용했으나 실행 속도 문제로 Playwright로 전환하였고, 언론사별 HTML 구조 차이에 대응하기 위해 여러 선택자를 순차적으로 적용하도록 구현했습니다.

### 4. GPT 기반 리포트 생성

수집한 주가, 뉴스, 환율 데이터를 OpenAI API에 전달하고 프롬프트를 통해 주요 내용을 분석 및 요약하도록 구성했습니다.

생성된 결과는 Slack에서 확인하기 쉬운 형태의 리포트로 변환하여 자동 전송합니다.

## Development Period

2025.06.16 ~ 2025.09.30

- Python 기초 학습: 2025.06.16 ~ 2025.07.27
- 프로젝트 개발: 2025.07.28 ~ 2025.09.30

## Role

개인 프로젝트

- 서비스 기획
- 데이터 수집 및 처리
- 크롤링 로직 구현
- OpenAI API 연동
- Slack 연동
- 자동화 스케줄링
- 테스트 및 디버깅

## Limitations

- 웹 페이지 구조 변경 시 크롤링 오류 발생 가능
- 언론사별 HTML 구조 차이에 따른 예외 발생 가능
- 전체 프로세스 실행에 약 15분 소요
- 현재 로컬 환경에서 실행

## What I Learned

- 정적/동적 웹 페이지 크롤링
- DOM 구조 분석 및 CSS Selector 활용
- 외부 API 연동
- 생성형 AI를 활용한 데이터 분석 자동화
- Slack Webhook 연동
- 자동화 파이프라인 설계
- 디버깅 및 예외 처리 경험

## 결과 화면

주가 데이터 JSON 파일 일부 캡처
<img width="2110" height="1054" alt="image" src="https://github.com/user-attachments/assets/5ddb3895-50de-42ba-803e-a2c4fb10ed5e" />
뉴스 기사 JSON 파일 일부 캡처
<img width="2112" height="1027" alt="image" src="https://github.com/user-attachments/assets/7c9b5b9d-33c5-4015-8c75-000475ce1b6d" />
Slack에 전송된 최종 리포트 캡처
<img width="2140" height="1115" alt="image" src="https://github.com/user-attachments/assets/90ec862f-a571-40e9-ba57-a7841ffb1900" />

