import schedule  # 작업을 일정 주기로 실행할 수 있게 해주는 외부 라이브러리
import time  # 시간 관련 기능 제공 
import requests  # 웹 페이지 요청용 라이브러리
from bs4 import BeautifulSoup  # HTML 파싱용 라이브러리
from datetime import datetime  # 현재 시간 기록용
import json  # JSON 파일 저장용
import re  # 정규표현식 처리용 모듈  
from playwright.sync_api import sync_playwright  # 실제 웹 브라우저처럼 동작하는 자동화 도구
import random  # 난수를 다루는 모듈
import os  # 파일/디렉토리 관리용 라이브러리
from openai import OpenAI  # OpenAI API 사용을 위한 라이브러리 (GPT 호출용)
import glob  # 파일 경로명 패턴을 이용해 파일/디렉토리 목록을 찾는 모듈

def sendSlackWebHook(strText):  # Slack 채널에 메시지를 보내는 함수
    slack_url = os.getenv("Slack_Url")  # Slack Webhook URL (환경변수에서 불러오기)
    headers = {
        "Content-type": "application/json"  # 요청 헤더: JSON 형식으로 전송
    }
    
    data = {
        "text": strText  # 실제로 보낼 메시지 (Slack 채널에 표시됨)
    }
    res = requests.post(slack_url, headers=headers, json=data)  # Slack Webhook URL로 POST 요청 전송

    if res.status_code == 200:  # Slack API 응답이 정상일 경우
        return "OK"
    else:  # 오류 발생 시
        return "Error" 

def get_article_content(page, article_url):  # 주어진 URL의 웹페이지에서 광고 등을 제외한 실제 기사 내용만 가져오는 함수
    #  지정된 URL의 기사 본문을 Playwright를 이용해 가져옴
    try:  # 오류가 발생해도 프로그램이 멈추지 않도록 하는 안전장치 시작
        page.goto(article_url, wait_until="domcontentloaded", timeout=20000)  # 주어진 URL로 이동. 20초 이상 걸리면 타임아웃 오류 발생

        # 여러 언론사에서 공통적으로 사용하는 본문 선택자(CSS Selector) 목록 준비
        article_selector = '[itemprop="articleBody"], article, [class*="article"], [id*="article"], [class*="content"], [id*="content"]'
        
        # 위 선택자 중 하나라도 페이지에 나타날 때까지 최대 20초간 기다림
        page.wait_for_selector(article_selector, state="attached", timeout=20000)

        html_content = page.content()  # 자바스크립트가 모두 실행된 후의 최종 HTML 코드를 가져옴
        soup = BeautifulSoup(html_content, "html.parser")  # 가져온 HTML을 BeautifulSoup으로 분석 준비

        # 우선순위에 따라 가능한 본문 영역을 차례대로 검색
        content_div = (
            soup.find(attrs={'itemprop': 'articleBody'})  # 1순위: itemprop='articleBody' 속성을 가진 태그
            or soup.find(class_=re.compile("article"))  # 2순위: 클래스 이름에 'article'이 포함된 태그
            or soup.find(class_=re.compile("content"))  # 3순위: 클래스 이름에 'content'가 포함된 태그
            or soup.find(id=re.compile("article"))  # 4순위: id에 'article'이 포함된 태그
            or soup.find(id=re.compile("content"))  # 5순위: id에 'content'가 포함된 태그
        )
        
        if content_div:  # 만약 본문 영역을 찾았다면
            return content_div.get_text(separator='\n', strip=True)  # 그 안의 텍스트만 추출하여 반환
        return "본문 파싱 실패"  # 위 모든 방법으로도 본문을 못 찾으면 실패 메시지 반환

    except Exception as e:  # 위 'try' 블록에서 어떤 종류든 오류가 발생하면
        print(f"예상치 못한 오류 발생: {e}")  # 오류 내용을 출력하고
        return "알 수 없는 오류로 실패"  # 실패 메시지를 반환 (프로그램은 계속 실행됨)

   
    
def make_json():  # 실행할 작업(함수): 주가 & 뉴스 데이터 수집 후 JSON 저장
    companies = [
        'QQQM',  # 나스닥100 ETF
        'SPLG',  # S&P500 ETF
        'TSLA',  # 테슬라
        'AAPL',  # 애플
        'META',  # 메타
        'NVDA',  # 엔비디아
        'GOOGL', # 구글 (Alphabet A)
        'MSFT'   # 마이크로소프트
    ]  # 조회할 종목 리스트  # 조회할 종목 리스트
    companies_stocks = {}  # 종목별 주가 정보를 담을 딕셔너리
    current_time = datetime.now().strftime("%Y-%m-%d_%H_%M")  # 현재 시간 기록

    # 주가 데이터 수집
    for company in companies:
        try:
            stock_url = f"https://finance.yahoo.com/quote/{company}/"  # 해당 종목의 야후 파이낸스 페이지 URL
            
            response = requests.get(stock_url,  # 해당 종목의 야후 파이낸스 페이지 URL
            headers = {"User-Agent": "Mozilla/5.0"},  # 봇 차단 회피용 헤더
            timeout = 15  # 최대 15초까지만 대기
            )
            html = response.text  # HTML 소스 요청
            soup = BeautifulSoup(html, "html.parser")  # HTML 파싱 객체 생성

            # 주요 주가 데이터 추출
            qsp_price = soup.find("span", {"data-testid": "qsp-price"}).text  # 현재가
            previous_close = soup.find("fin-streamer", {"data-field": "regularMarketPreviousClose"}).text  # 전일 종가
            market_open = soup.find("fin-streamer", {"data-field": "regularMarketOpen"}).text  # 시가
            day_range = soup.find("fin-streamer", {"data-field": "regularMarketDayRange"}).text  # 당일 저가-고가 범위
            fifty_two_range = soup.find("fin-streamer", {"data-field": "fiftyTwoWeekRange"}).text  # 52주 저가-고가 범위
            volume = soup.find("fin-streamer", {"data-field": "regularMarketVolume"}).text  # 거래량
            avg_volume = soup.find("fin-streamer", {"data-field": "averageVolume"}).text  # 평균 거래량

            stock = {  # 한 종목의 정보를 딕셔너리로 저장
                '현재 시간' : current_time,
                '현재가': f"${qsp_price}",
                '전일 종가' : f"${previous_close}",
                '시가': f"${market_open}",
                '저가-고가': f"${day_range}",
                '52주 저가-고가': f"${fifty_two_range}",
                '거래량': volume,
                '평균 거래량' : avg_volume
            }

            companies_stocks[company] = stock  # 종목별 데이터 저장
        except Exception as e:  # 오류 발생 시
            print("stock_fail:", company, e)  # 실패 및 오류 메시지 출력
            continue  # 스킵
    
    # 주가 JSON 저장    
    save_dir_1 = r"C:\Users\sta12\workspace\stocks_jsons"  # 저장할 경로
    os.makedirs(save_dir_1, exist_ok=True)  # 디렉토리 없으면 생성
    filepath = os.path.join(save_dir_1, f"stocks_{current_time}.json")  # 파일 전체 경로 만들기
    
    if companies_stocks:
        with open(filepath, "w", encoding="utf-8") as f:  # JSON 파일로 저장
            json.dump(companies_stocks, f, ensure_ascii=False, indent=4)
        print("주가 데이터 수집 완료")  # 완료 메시지 출력 
#------------------------------------------------------------------------------------------------------------------------------
    # 뉴스 데이터 수집
    companies = ['테슬라','애플','메타','엔디비아','구글','마이크로소프트']  # 기업명 리스트
    companies_articles = {}  # 전체 결과 저장 딕셔너리
    pages = 3  # 네이버 뉴스 검색 결과에서 가져올 페이지 수
    # Playwright 시스템을 켜고, 모든 작업이 끝나면 자동으로 꺼주는 'with' 구문 시작
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # 눈에 보이지 않는 크롬(Chromium) 브라우저 실행
        article_page = browser.new_page()
        for company in companies:
            all_articles = {}  # 모든 기사 제목, URL, 본문을 저장할 빈 딕셔너리 생성
            current_time = datetime.now()  # 현재 시간 기록
            print(f"'{company}' 뉴스 기사 본문 수집 시작")

            article_count = 1  # 전체 기사 번호를 매기기 위한 카운터 변수
            # 1페이지부터 설정한 페이지 수(PAGES_TO_SCRAPE)까지 반복
            for page_num in range(1, pages + 1):
                start_num = (page_num - 1) * 10 + 1  # 네이버 뉴스 페이지 번호(1, 11, 21...) 계산

                # 네이버 뉴스 검색 결과 페이지 URL 생성
                search_url = f"https://search.naver.com/search.naver?where=news&sm=tab_pge&query={company}&start={start_num}"

                # requests를 이용해 검색 결과 페이지에 접속 
                response = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"},timeout = 15)
                soup = BeautifulSoup(response.text, 'html.parser')  # 가져온 HTML을 BeautifulSoup으로 분석 준비

                news_items = soup.find_all("span", class_=re.compile("headline1"))

                # 찾은 기사 목록을 하나씩 순회
                for item in news_items:
                    if item:  # item이 비어있지 않다면
                        parent_a = item.find_parent("a")  # 해당 item을 감싸고 있는 부모 <a> 태그(링크)를 찾음
                        title = parent_a.get_text(strip=True)  # <a> 태그 안의 텍스트(기사 제목)를 가져옴
                        url = parent_a['href']  # <a> 태그의 href 속성(기사 원문 URL)을 가져옴
                        print(f"  {article_count}. '{title}' 기사 본문 수집 중")

                        content = get_article_content(article_page, url)  # 새로 만든 탭으로 기사 본문 수집
                        all_articles[str(article_count)] = {   # 수집한 제목, URL, 본문을 딕셔너리 형태로 저장
                            "title": title,
                            "url": url,
                            "content": content
                        }
                        article_count += 1  # 다음 기사 번호를 위해 1 증가       
                    time.sleep(random.uniform(0.5, 1.5)) 
            companies_articles[company] = all_articles
        
        article_page.close()
        browser.close()  # 모든 페이지 반복이 끝나면 브라우저를 닫음
        
    if companies_articles:  # 수집된 기사가 하나라도 있다면
        datetimes = current_time.strftime("%Y-%m-%d_%H-%M")  # 파일 이름에 사용할 날짜/시간 문자열 생성
        save_dir_2 = r"C:\Users\sta12\workspace\articles_jsons"
        os.makedirs(save_dir_2, exist_ok=True)  # 저장할 폴더가 없으면 자동으로 생성
        filepath = os.path.join(save_dir_2, f"articles_{datetimes}.json")  # 최종 파일 경로 생성

        # 파일을 쓰기 모드('w')로 열고, 한글 처리를 위해 인코딩을 'utf-8'로 설정
        with open(filepath, "w", encoding="utf-8") as f:
            # 딕셔너리 데이터를 JSON 파일로 저장
            json.dump(companies_articles, f, ensure_ascii=False, indent=4)

        print("뉴스기사 수집 완료")
    else:  # 수집된 기사가 하나도 없다면
        print("수집된 기사가 없습니다.")
        
    return companies_stocks, companies_articles
 
        
def krw_exchange():  # 금일 환율 정보를 가져오는 함수
    exchange_url = "https://search.naver.com/search.naver?where=nexearch&query=환율"  # 네이버 환율 검색 페이지의 URL 주소
    headers = {"User-Agent": "Mozilla/5.0"}  # 봇 차단용 헤더
    response = requests.get(exchange_url, headers=headers, timeout=15)  # 지정된 URL로 GET 요청을 보내고 응답을 받음 (최대 15초 대기)
    soup = BeautifulSoup(response.text, "html.parser")  # 받아온 HTML 텍스트를 파싱(분석)하기 쉽게 BeautifulSoup 객체로 변환
    span = soup.select_one('span.nb_txt._pronunciation[data-currency-unit="원"]')  # CSS 선택자를 사용해 환율 정보가 있는 특정 <span> 태그를 찾음
    krw = span.get_text(strip=True).replace("원", "KRW")  # 찾은 태그에서 텍스트를 추출하고 '원'을 'KRW'로 바꿈
    
    return krw

    
def gpt_stock():  # GPT 호출 및 분석 함수'
    api_key = os.getenv("OPENAI_API_KEY")  # 환경변수에서 OpenAI API 키 불러오기
    if not api_key:  # API 키가 없으면
        sendSlackWebHook("*에러* OPENAI_API_KEY 오류")  # 슬랙으로 에러 메시지 전송
        return  # 함수 종료
    client = OpenAI(api_key=api_key)  # OpenAI 클라이언트 객체 생성
    stocks, articles = make_json()  # 주가 데이터와 뉴스 데이터 가져오기
    krw = krw_exchange()
    
    # GPT 호출
    try:
        response = client.chat.completions.create(  # GPT 모델 호출
            model="gpt-5",  # 사용할 모델 지정
            messages=[
                {
                    "role": "system",  # 시스템 프롬프트
                    "content": (
                        "You are a professional financial analyst and reporting assistant. "
                        "Your role is to transform raw stock data and related news about foreign-listed companies "
                        "and ETFs into concise, decision-ready market summaries.\n\n"

                        "Guidelines:\n"
                        "1. Structure output strictly by ticker/company/ETF name.\n"
                        "2. For each entity, summarize stock metrics: current price, open, previous close, "
                        "intraday low–high range, 52-week low–high range, and trading volume (highlight unusual activity).(with KRW conversion in parentheses using today's FX rate)\n"
                        "3. For ETFs (e.g., QQQM, SPLG): if direct news is unavailable, infer context from index performance, "
                        "top holdings (AAPL, MSFT, NVDA, GOOGL, META, TSLA, etc.), sector movements, or macroeconomic drivers "
                        "(interest rates, CPI, Fed, USD, oil).\n"
                        "4. Rigorously filter news: include only items that directly affect price action or sentiment. "
                        "Exclude irrelevant, generic, or tangential headlines.\n"
                        "5. Synthesize: explicitly connect price movements with potential drivers (earnings, regulation, "
                        "product launches, partnerships, macro events).\n"
                        "6. Output format must be clean Markdown optimized for Slack in Korean:\n"
                        "   - **Ticker / Company or ETF Name**\n"
                        "     - Stock Summary: ...\n"
                        "     - Key News: ...\n"
                        "     - Outlook: ...\n\n"
                        "Goal: Deliver clear, reliable, and timely insights that executives can absorb in seconds."
                    )
                },
                {
                    "role": "user",  # 유저 프롬프트
                    "content": (
                        f"아래는 두 가지 데이터셋과 오늘의 환율 정보야.\n\n"
                        f" 최신 뉴스 데이터:\n{json.dumps(articles, ensure_ascii=False, indent=2)}\n\n"
                        f" 관련 주가 데이터:\n{json.dumps(stocks, ensure_ascii=False, indent=2)}\n\n"
                        f" 오늘의 환율:\n1 USD = {krw}\n\n" 

                        "작성 규칙:\n"
                        "- 제공된 '오늘의 환율'을 사용해 모든 달러 가격 옆에 원화 환산 금액을 (₩000,000) 형식으로 반드시 표기해.\n"
                        "- 기업(테슬라, 애플, 엔비디아, 구글, 메타, 마이크로소프트)과 ETF(QQQM, SPLG)를 모두 포함하고, 뉴스가 없으면 '관련 뉴스 없음'으로 명시해.\n"
                        "- ETF는 직접 뉴스가 부족하면 구성 종목·추종 지수·거시 변수 등을 근거로 해석해.\n"
                        "- 주가 요약 시 '거래량'은 평균 거래량과 비교하여 \"(평균 대비 +15.2%)\" 또는 \"(평균 대비 -8.9%)\" 와 같이 소수점 첫째 자리까지 정량적으로 표현해.\n"
                        "- '핵심 뉴스'는 각 항목 앞에 [호재] 또는 [악재] 태그를 붙여 긍정/부정 요인을 명확히 구분해.\n"
                        "- '전망'은 단기적(1-4주) 관점에서의 전망을 한 줄로 정리해.\n"
                        "- 마지막에 모든 종목의 전망을 한 줄씩 요약한 '종합 전망' 섹션을 추가해.\n"
                        "- 전체 출력은 Slack에 최적화된 Markdown 형식의 한국어로 작성해."
                    )
                }
            ]
        )
        g_report = response.choices[0].message.content 
        today = datetime.now().strftime("%Y-%m-%d")  # 파일 이름에 사용할 날짜 문자열 생성
        save_dir_3 = r"C:\Users\sta12\workspace\report_txts"
        os.makedirs(save_dir_3, exist_ok=True)  # 저장할 폴더가 없으면 자동으로 생성
        filepath = os.path.join(save_dir_3, f"gpt_report_{today}.txt")  # 최종 파일 경로 생성
        # 파일을 쓰기 모드('w')로 열고, 한글 처리를 위해 인코딩을 'utf-8'로 설정
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(g_report)  #  데이터를 텍스트 파일로 저장
            
        print("리포트 저장 완료")
        
    except Exception as e:  # 예외 발생 시
        print("GPT 호출 실패", e)  # 콘솔에 출력
        sendSlackWebHook(f"GPT 호출 실패: {e}")  # 슬랙으로 알림
        return  # 함수 종료
    
def _latest_file(folder, pre):  # 폴더 내에서 가장 최근 txt 파일 찾는 함수
    paths = glob.glob(os.path.join(folder, f"{pre}*.txt"))   # fir로 시작하는 모든 .txt 파일 리스트
    return max(paths, key=os.path.getmtime) if paths else None   # 가장 최근 수정된 파일 반환 (없으면 None)    
    
def msg_slack():  # 생성된 리포트를 슬랙으로 전송하는 함수
    today = datetime.now().strftime("%Y-%m-%d")
    # 최신 GPT 리포트 파일 열기
    report_path = _latest_file(r"c:\Users\sta12\workspace\report_txts", f"gpt_report_{today}")  # 최신 리포트 txt 파일 경로 찾기
    if not report_path:  # 파일이 없을시
        sendSlackWebHook("*오류* 금일 report_txts 폴더에 파일이 생성되지 않았습니다")  # 슬랙 알림 전송
        return  # 함수 종료
    with open(report_path, "r", encoding="utf-8") as f:  # 리포트 txt 파일 읽기
        report_data = f.read()  # txt → 파이썬 객체로 변환

        sendSlackWebHook(report_data) # 리포트 내용을 슬랙으로 전송
        
   

if __name__ == "__main__":  # 메인 실행부
    schedule.every().day.at("17:04").do(gpt_stock)# 매일 08:40에 gpt_stock 실행 예약
    schedule.every().day.at("17:24").do(msg_slack)# 매일 09:00에 msg_slack 실행 예약

    while True:  # 무한 루프 (스케줄러 동작 유지)
        schedule.run_pending()  # 예약된 작업 실행
        time.sleep(1)  # 1초 대기 (과도한 CPU 점유 방지)

