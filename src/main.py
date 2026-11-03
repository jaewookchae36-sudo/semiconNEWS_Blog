import os
import datetime
import json
import feedparser
import requests
from openai import OpenAI

RSS_FEEDS = {
    '구글뉴스(반도체)': 'https://news.google.com/rss/search?q=반도체+when:1d&hl=ko&gl=KR&ceid=KR:ko',
    '구글뉴스(삼성전자)': 'https://news.google.com/rss/search?q=삼성전자+반도체+when:1d&hl=ko&gl=KR&ceid=KR:ko',
    '구글뉴스(SK하이닉스)': 'https://news.google.com/rss/search?q=SK하이닉스+반도체+when:1d&hl=ko&gl=KR&ceid=KR:ko',
    '구글뉴스(TSMC)': 'https://news.google.com/rss/search?q=TSMC+반도체+when:1d&hl=ko&gl=KR&ceid=KR:ko',
    '구글뉴스(엔비디아)': 'https://news.google.com/rss/search?q=엔비디아+반도체+when:1d&hl=ko&gl=KR&ceid=KR:ko'
}

HEADERS = {'User-Agent': 'Mozilla/5.0'}

def collect_news():
    articles = []
    print("[1/4] 구글 뉴스 RSS 피드 수집 중...")
    for source, url in RSS_FEEDS.items():
        try:
            res = requests.get(url, headers=HEADERS, timeout=5)
            res.raise_for_status()
            feed = feedparser.parse(res.content)
            for entry in feed.entries[:5]:
                title = getattr(entry, 'title', '제목 없음')
                link = getattr(entry, 'link', '')
                articles.append(f"[{source}] {title} ({link})")
        except Exception as e:
            print(f"[{source}] 수집 건너뜀: {e}")
    return articles

def generate_blog_content(articles):
    print("[2/4] OpenAI (gpt-4o-mini)로 블로그 본문 생성 중...")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        
    client = OpenAI(api_key=api_key)
    
    # 안정적이므로 기사를 25개까지 넉넉하게 보냅니다.
    raw_text = "\n".join(articles[:25])
    today_str = datetime.datetime.now().strftime("%Y년 %m월 %d일")
    
    system_prompt = """
    당신은 반도체 산업 전문 블로거입니다. 
    오늘 수집된 뉴스를 바탕으로 구글 검색에 잘 노출되는 롱폼 블로그 포스트를 마크다운(Markdown)으로 작성하세요.

    [마크다운 콘텐츠 구조]
    - 서론: 오늘 반도체 시장 흐름 2~3문장 요약 (인용구 `>` 사용)
    - 본론 1~4: 주요 섹터별(메모리, 파운드리, 소부장, AI) 상세 이슈 정리. H2(`##`), H3(`###`) 태그 활용. 기사 원문 링크 연결.
    - 본론 5 (핵심): 언급된 **관련 기업 및 필수 반도체 용어 정리** (마크다운 표 `|---|` 사용)
    - 결론: 산업적 시사점 및 투자 인사이트
    """

    user_prompt = f"""
    반드시 JSON 형식으로만 응답하세요. 
    키는 "title" (검색 유입이 잘 되도록 날짜 {today_str} 포함)과 "content" (완벽한 마크다운) 두 개입니다.

    수집된 기사:
    {raw_text}
    """

    # 가장 저렴하고 빠르며 절대 멈추지 않는 gpt-4o-mini 모델
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    
    post_data = json.loads(response.choices[0].message.content)
    return post_data['title'], post_data['content']

def save_to_markdown(title, content):
    print("[3/4] 마크다운 파일 생성 중...")
    now = datetime.datetime.now()
    
    date_str = now.strftime("%Y-%m-%d")
    import re
    safe_title = re.sub(r'[^가-힣A-Za-z0-9\s]', '', title).strip().replace(' ', '-')
    filename = f"_posts/{date_str}-{safe_title}.md"
    
    if len(filename) > 100:
        filename = f"_posts/{date_str}-daily-semicon-news.md"
    
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
        print("수집된 뉴스가 없습니다.")
        return
        
    title, content = generate_blog_content(articles)
    save_to_markdown(title, content)
    print("[4/4] 로컬 파일 쓰기 완료. GitHub Actions가 커밋을 진행합니다.")

if __name__ == "__main__":
    main()
