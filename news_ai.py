# news_ai.py — חדשות + ניתוח AI
import streamlit as st
import yfinance as yf


def _analyze(title: str) -> str:
    t = title.lower()
    if any(w in t for w in ["earning", "revenue", "profit", "beat", "miss", "q1","q2","q3","q4"]):
        return "**📝 עדכון כספי.**\n\n**🔍 AI:** בדוק שצמיחה >10% (קריטריון 1)."
    elif any(w in t for w in ["ai", "chip", "cloud", "tech", "launch"]):
        return "**📝 חדשנות/השקה.**\n\n**🔍 AI:** מחזקת את ה'חפיר הכלכלי'. תומכת בצמיחה."
    elif any(w in t for w in ["buy", "upgrade", "bull", "target", "rally", "soar"]):
        return "**📝 סנטימנט חיובי.**\n\n**🔍 AI:** שדרוג אנליסטים. ודא שהמחיר מתחת לשווי הוגן."
    elif any(w in t for w in ["sell", "downgrade", "bear", "drop", "fall", "lawsuit"]):
        return "**📝 סנטימנט שלילי.**\n\n**🔍 AI:** אם המאזן חזק — זו הזדמנות לאיסוף."
    elif any(w in t for w in ["dividend", "payout", "yield"]):
        return "**📝 דיבידנד.**\n\n**🔍 AI:** מאשר חוזק תזרים מזומנים — קריטריון 6."
    return "**📝 עדכון שוטף.**\n\n**🔍 AI:** רעשי רקע. דבוק באסטרטגיית ה-PDF."


def render_live_news(symbols_list: list):
    st.markdown(
        '<div class="ai-card" style="border-right-color: #f50057;">'
        '<b>📰 חדשות בזמן אמת + ניתוח AI:</b></div>',
        unsafe_allow_html=True,
    )

    top = symbols_list[:4]
    cols = st.columns(2)

    for i, sym in enumerate(top):
        with cols[i % 2]:
            st.markdown(f"### 🏢 {sym}")
            try:
                news = yf.Ticker(sym).news or []
                if news:
                    for article in news[:2]:
                        title = article.get("title", "")
                        if not title and "content" in article:
                            title = article["content"].get("title", "עדכון שוק")
                        publisher = article.get("publisher", "")
                        if not publisher and "content" in article:
                            publisher = article["content"].get("provider", {}).get("displayName", "מקור")
                        link = article.get("link", "#")
                        if not link and "content" in article:
                            link = article["content"].get("clickThroughUrl", {}).get("url", "#")

                        with st.container(border=True):
                            st.caption(f"מקור: {publisher} | [קרא עוד]({link})")
                            st.markdown(f"##### {title}")
                            st.markdown(_analyze(title))
            except Exception:
                st.warning(f"לא ניתן לשאוב חדשות עבור {sym}.")
