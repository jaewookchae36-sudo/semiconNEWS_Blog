# 반도체 뉴스 블로그 🚀

이곳은 매일 반도체 산업 동향이 자동으로 업데이트되는 블로그입니다.

---

## 📝 최신 뉴스 리포트
<ul>
  {% for post in site.posts %}
    <li style="margin-bottom: 10px;">
      <a href="{{ post.url | relative_url }}" style="font-size: 1.1em; font-weight: bold;">{{ post.title }}</a>
      <br>
      <span style="color: gray; font-size: 0.9em;">{{ post.date | date: "%Y년 %m월 %d일" }}</span>
    </li>
  {% endfor %}
</ul>

<meta name="naver-site-verification" content="07743e70f1830ac76ecfea337a2794133c5fd578" />
