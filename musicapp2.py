import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import urllib.parse
import os

# ---------- 資料讀取 ----------
DATA_PATH = "./musical_titles_all.xlsx"

if not os.path.exists(DATA_PATH):
    st.error(f"找不到檔案：{DATA_PATH}，請確認檔案與您的 .py 程式檔放在同一個資料夾。")
    st.stop()

try:
    musicals = pd.read_excel(DATA_PATH)
except Exception as e:
    st.error(f"讀取 Excel 檔案時發生錯誤：{e}")
    st.stop()

# ---------- 問卷題目 ----------
questions = {
    "開放性": ["我喜歡奇幻想像的劇情", "我偏好新穎、實驗性強的作品"],
    "嚴謹性": ["我會查閱表演背景", "我在意劇情邏輯"],
    "外向性": ["我喜歡熱鬧華麗的歌舞", "我偏好與朋友一起觀賞"],
    "親和性": ["我容易被情感感動", "我喜歡溫暖人性關懷的故事"],
    "神經質": ["我偏好張力強、懸疑劇情", "劇情高潮時我會感到緊張"]
}

# ---------- 0915統一推薦理由 ----------
def generate_general_reason(user_scores):
    sorted_traits = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
    top_traits = [trait for trait, score in sorted_traits[:2]]

    trait_descriptions = {
        "開放性": "你對創新與奇幻想像特別敏感，適合探索風格獨特的音樂劇",
        "嚴謹性": "你重視劇情邏輯與背景，適合結構完整、敘事嚴謹的作品",
        "外向性": "你喜歡熱鬧氛圍與社交互動，適合華麗歌舞與群體觀賞的劇目",
        "親和性": "你容易被情感觸動，適合溫暖人性、關懷社會的故事",
        "神經質": "你偏好張力與懸疑，適合情緒起伏強烈的劇情設計"
    }

    reasons = [trait_descriptions[t] for t in top_traits if t in trait_descriptions]
    return "｜".join(reasons)

# ---------- 分數雷達圖 + 統一推薦理由 ----------
def plot_user_traits_with_reason(traits_scores):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=list(traits_scores.values()),
        theta=list(traits_scores.keys()),
        fill='toself',
        name='你的人格特質'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[1, 5])),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

    general_reason = generate_general_reason(traits_scores)
    # st.markdown(f"🧠 **推薦理由：** {general_reason}")

    st.markdown(f"""
    <style>
        .big-font {{
            font-size: 28px !important;
            color: royalblue;
        }}
        .big-font1 {{
            font-size: 20px !important;
            color: royalblue;
        }}
    </style>
    <p class='big-font'>🧠 <strong>推薦理由：</strong></p><p class='big-font1'> {general_reason}</p>
    """, unsafe_allow_html=True)


# ---------- UI ----------
st.set_page_config(page_title="人格測驗音樂劇推薦", layout="wide")
st.title("🎭 人格測驗音樂劇推薦系統")

# 使用者輸入
user_scores = {}
with st.sidebar:
    st.header("🧪 請輸入你的偏好分數")
    for trait, qs in questions.items():
        scores = []
        st.subheader(trait)
        for q in qs:
            score = st.slider(q, 1, 5, 3)
            scores.append(score)
        user_scores[trait] = sum(scores) / len(scores)
    submit = st.button("產生推薦")

# ---------- 主畫面 ----------
if submit:
    st.subheader("📊 你的人格特質雷達圖")
    plot_user_traits_with_reason(user_scores)

    traits = list(questions.keys())
    required_cols = traits + ['作品名稱', '類型', '作品內容介紹', '作品韓文名稱', '訊息連結', '圖片連結']
    if not all(col in musicals.columns for col in required_cols):
        st.error(f"您的 Excel 檔案中缺少必要的欄位！請確認檔案包含以下欄位：{required_cols}")
        st.stop()

    musicals[traits] = musicals[traits].apply(pd.to_numeric, errors='coerce')

    def score_diff(row):
        return sum(abs(row[trait] - user_scores[trait]) if pd.notnull(row[trait]) else 5 for trait in traits)

    musicals["score_diff"] = musicals.apply(score_diff, axis=1)
    top_musicals = musicals.sort_values("score_diff").head(5)

    st.subheader("🎬 推薦音樂劇")
    for _, row in top_musicals.iterrows():
        st.markdown(f"### {row['作品名稱']}")
        col1, col2 = st.columns([2, 1])

        with col1:
            st.write(f"**類型：** {row['類型']}")
            st.write(f"**介紹：** {row['作品內容介紹']}")
            korean_name = row['作品韓文名稱']
            if pd.notna(korean_name) and str(korean_name).strip() != "":
                encoded_name = urllib.parse.quote(str(korean_name))
                st.markdown(f"[🔗 在 KOPIS 上查看《{korean_name}》的更多資訊]")
                st.link_button("立即前往", row['訊息連結'])
        with col2:
            st.image(row['圖片連結'], width=320)

        st.markdown("---")