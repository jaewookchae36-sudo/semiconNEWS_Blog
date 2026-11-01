import os
import datetime
import json
import re
import feedparser
import requests
from google import genai

RSS_FEEDS = {
    '디지털데일리': 'https://www.ddaily.co.kr/news/rss_section.html?section_code=01700',
    '전자신문': 'https://www.etnews.com/rss/010.xml',
    '지디넷코리아': 'https://zdnet.co.kr/rss/news_section.xml?sec=0002',
    'SemiAnalysis': 'https://www.semianalysis.com/feed',
    '삼성전자': 'https://news.samsung.com/kr/feed',
    'SK하이닉스': 'https://news.skhynix.co.kr/feed'
}

HEADERS = {'User-Agent': 'Mozilla/5.0'}

def collect_news():
    articles = []
    print("[1/4] RSS 피드 뉴스 수집 중...")
    for source, url in RSS_FEEDS.items():
        try:
            res = requests.get(url, headers=HEADERS, timeout=5)
            res.raise_for_status()
            feed = feedparser.parse(res.content)
            for entry in feed.entries[:4]:
                title = getattr(entry, 'title', '제목 없음')
                link = getattr(entry, 'link', '')
                articles.append(f"[{source}] {title} ({link})")
        except Exception as e:
            print(f"[{source}] 수집 건너뜀: {e}")
    return articles

def generate_blog_content(articles):
    print("[2/4] Gemini API로 SEO 최적화 블로그 본문 생성 중...")
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    raw_text = "\n".join(articles[:25])
    today_str = datetime.datetime.now().strftime("%Y년 %m월 %d일")
    
    prompt = f"""
    당신은 반도체 산업 전문 블로거입니다. 
    오늘 수집된 뉴스를 바탕으로 구글 검색에 잘 노출되는 롱폼 블로그 포스트를 작성하세요.

    [작성 규칙]
    1. 반드시 JSON 형식으로 응답하세요. 키는 "title"과 "content" 입니다.
    2. "title"은 검색 유입이 잘 되도록 구체적인 키워드와 날짜({today_str})를 포함하세요.
    3. "content"는 완벽한 마크다운(Markdown) 형식으로 작성하세요.

    [마크다운 콘텐츠 구조]
    - 서론: 오늘 반도체 시장 흐름 2~3문장 요약 (인용구 `>` 사용)
    - 본론 1~4: 주요 섹터별(메모리, 파운드리, 소부장, AI) 상세 이슈 정리. H2(`##`), H3(`###`) 태그 활용. 기사 원문 링크 연결.
    - 본론 5 (핵심): 언급된 **관련 기업 및 필수 반도체 용어 정리** (마크다운 표 `|---|` 사용)
    - 결론: 산업적 시사점 및 투자 인사이트

    [수집된 기사]
    {raw_text}
    """

    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
    )
    
    clean_json = re.sub(r'^```json\n|```$', '', response.text.strip(), flags=re.MULTILINE)
    post_data = json.loads(clean_json)
    return post_data['title'], post_data['content']

def save_to_markdown(title, content):
    """Jekyll 규격에 맞춰 _posts 폴더에 md 파일 생성"""
    print("[3/4] 마크다운 파일 생성 중...")
    now = datetime.datetime.now()
    
    # 파일명 규칙: YYYY-MM-DD-제목.md (Jekyll 필수 규칙)
    date_str = now.strftime("%Y-%m-%d")
    # 파일명에서 특수문자 제거 및 띄어쓰기를 하이픈으로 변경
    safe_title = re.sub(r'[^가-힣A-Za-z0-9\s]', '', title).strip().replace(' ', '-')
    filename = f"_posts/{date_str}-{safe_title}.md"
    
    # 파일명 길이가 너무 길어지지 않게 조절
    if len(filename) > 100:
        filename = f"_posts/{date_str}-daily-semicon-news.md"
    
    # 상단 메타데이터(Front Matter) 추가
    front_matter = f"""---
layout: post
title: "{title}"
date: {now.strftime("%Y-%m-%d %H:%M:%S +0900")}
categories: [반도체, 일일브리핑]
tags: [반도체, HBM, 파운드리, AI반도체, 주식]
---

"""
    os.makedirs("_posts", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(front_matter + content)
    
    print(f"✅ 파일 생성 완료: {filename}")

def main():
    print("=== GitHub Pages 블로그 자동화 시작 ===")
    articles = collect_news()
    if not articles:
        return
        
    title, content = generate_blog_content(articles)
    save_to_markdown(title, content)
    print("[4/4] 로컬 파일 쓰기 완료. GitHub Actions가 커밋을 진행합니다.")

if __name__ == "__main__":
    main()
