import streamlit as st
from supabase import create_client, Client
import openai

# ---- 환경설정 ----
st.set_page_config(page_title="AI 프로젝트 통합앱", page_icon="🤖", layout="centered")
OPENAI_API_KEY = st.secrets["openai"]["api_key"]
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

client = openai.OpenAI(api_key=OPENAI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========== Supabase DB 함수 ==========
def insert_report(student_id, student_name, student_report, ai_feedback, thought_change):
    data = {
        "student_id": student_id,
        "student_name": student_name,
        "student_report": student_report,
        "ai_feedback": ai_feedback,
        "thought_change": thought_change,
    }
    supabase.table("student_report2").insert(data).execute()

def update_thought_change(student_id, student_name, thought_change):
    reports = supabase.table("student_report2").select("id,created_at").eq("student_id", student_id).eq("student_name", student_name).order("created_at", desc=True).limit(1).execute()
    if reports.data:
        report_id = reports.data[0]['id']
        supabase.table("student_report2").update({"thought_change": thought_change}).eq("id", report_id).execute()

def get_reports():
    result = supabase.table("student_report2").select("*").order("created_at", desc=True).limit(50).execute()
    return result.data

# ========== 본문 ==========
st.title("아두이노와 인공지능을 활용한 외계행성계 탐사")
st.markdown("#### 학생 프로젝트 보고서 제출 및 AI 피드백 플랫폼")

with st.expander("📝 **보고서 작성 가이드 보기**", expanded=False):
    st.markdown("""
1. **나의 진로 탐색**  
    • 내가 관심 있는 진로 또는 직업은 무엇인가요?  
    • 그 직업이나 분야에 대해 간단히 설명해보세요.

    ✍️ **작성 예시:**  
    저는 스포츠 재활 트레이너가 되고 싶습니다. 선수들의 부상 회복을 돕고, 운동 능력을 분석하여 재활 계획을 세우는 직업입니다.

---

2. **해결하고 싶은 문제 찾기**  
    • 이 진로 분야에서 현재 어떤 문제나 불편함이 있을까요?  
    • 혹은 사람들을 더 돕기 위해 어떤 기술이 필요할까요?

    ✍️ **작성 예시:**  
    선수들의 몸 상태를 매일 확인하는 것이 어렵고, 부상 위험을 미리 알 수 없다는 문제가 있습니다.

---

3. **아두이노(센서)의 활용 방안**  
    • 어떤 센서를 사용하면 문제를 감지하거나 데이터를 수집할 수 있을까요?  
    • 그 센서는 무엇을 측정하고 어떤 정보를 줄 수 있을까요?

    ✍️ **작성 예시:**  
    근전도 센서를 이용하면 근육 사용량을 측정할 수 있습니다. 아두이노에 연결하면 운동 중 근육의 긴장도를 실시간으로 알 수 있습니다.

---

4. **인공지능의 역할**  
    • 인공지능(ChatGPT API 등)을 어떻게 활용할 수 있을까요?  
    • 수집한 데이터를 바탕으로 어떤 판단이나 조언을 할 수 있나요?

    ✍️ **작성 예시:**  
    수집된 데이터를 AI가 분석해서 “이 운동 자세는 부상 위험이 있습니다”와 같은 피드백을 제공할 수 있습니다.

---

5. **시스템의 작동 과정**  
    • 전체 기술 흐름(입력 → 처리 → 출력)을 정리해 보세요.  
    • 그림이나 도식으로 나타내도 좋습니다.

    ✍️ **작성 예시 (텍스트):**  
    센서 → 아두이노 → 데이터 수집 → ChatGPT API 분석 → 결과(경고 메시지, 조명, 소리 등)

---

6. **기대 효과 및 한계**  
    • 이 시스템이 실제로 사용된다면 어떤 긍정적인 효과가 있을까요?  
    • 기술적, 윤리적, 현실적 한계는 무엇일까요?

    ✍️ **작성 예시:**  
    운동 중 실시간 피드백을 받아 부상을 예방할 수 있습니다. 하지만 센서 정확도나 데이터 해석의 신뢰성 문제가 있습니다.

---

7. **느낀 점과 향후 계획**  
    • 이번 프로젝트나 활동을 통해 어떤 점을 배웠나요?  
    • 앞으로 어떤 기술이나 분야를 더 배우고 싶나요?

    ✍️ **작성 예시:**  
    센서와 AI가 단순히 이론이 아닌 실제 문제 해결에 도움이 된다는 것을 느꼈습니다. 앞으로는 영상 분석 AI도 배워보고 싶습니다.
""")

with st.form("report_form", clear_on_submit=False):
    st.subheader("1. 나의 진로 분야에서 아두이노(센서)와 인공지능의 활용 방안")
    student_id = st.text_input("학번", max_chars=20)
    student_name = st.text_input("이름", max_chars=20)
    student_report = st.text_area("보고서를 작성해 주세요.", height=200, key="student_report")

    submitted = st.form_submit_button("제출하기")
    ai_feedback = ""
    thought_change = ""

    if submitted:
        with st.spinner("AI 피드백 생성중..."):
            try:
                system_prompt = '''너는 고등학교 수준의 프로젝트 기반 학습을 지도하는 교사입니다.  
학생이 작성한 아래의 보고서를 성실히 읽고, 아래 기준에 따라 긍정적이고 구체적인 피드백을 작성해 주세요.

[보고서 분석 기준]  
1. 진로 탐색: 학생이 관심 진로를 얼마나 구체적이고 진지하게 탐색했는가?  
2. 문제 정의: 해당 진로 분야에서의 문제를 명확하게 인식하고 있는가?  
3. 기술 활용 아이디어: 아두이노(센서)와 인공지능(AI)을 얼마나 창의적이고 현실적으로 연결했는가?  
4. 전체 시스템 흐름: 입력 → 처리 → 출력의 과정을 논리적으로 설명했는가?  
5. 기대 효과 및 한계 인식: 기술이 줄 수 있는 긍정적 영향과 한계에 대한 균형 있는 시각을 갖고 있는가?  
6. 느낀 점과 태도: 프로젝트를 통해 학생이 어떤 성장을 이루었는지, 태도나 관심의 변화가 있는가?

[보고서 분석 목적]  
- 비판보다는 칭찬과 격려 중심의 피드백을 주세요.
- 구체적인 강점을 짚어주고, 발전 방향에 대해 제안해 주세요.
- 학생이 성취감을 느끼고, 다음 프로젝트에 더 자신감을 가질 수 있도록 도와주세요. 학생이 보고서 내용 속에서 더 생각해볼 내용을 딱 1가지는 포함해 주세요. 바로 학생들이 보는 글이기 때문에 피드백이 어떻게 생성되었는지는 절대 설명하지 마세요.'''
                user_prompt = f"학생 이름: {student_name}\n\n1. 학생 보고서 내용 :\n{student_report}"

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                )
                ai_feedback = response.choices[0].message.content
            except Exception as e:
                ai_feedback = f"AI 피드백 생성에 실패했습니다: {e}"

        insert_report(student_id, student_name, student_report, ai_feedback, thought_change)
        st.session_state["ai_feedback"] = ai_feedback
        # 아래 두 줄 추가!
        st.session_state["student_id"] = student_id
        st.session_state["student_name"] = student_name
        st.success("보고서 제출이 완료되었습니다!")

# AI 피드백, 수정/느낀점 폼
if st.session_state.get("ai_feedback"):
    st.markdown("---")
    st.subheader("2. 피드백 내용")
    st.text_area("AI 피드백", value=st.session_state["ai_feedback"], height=200, disabled=True)

    with st.form("thought_change_form"):
        st.subheader("3. 피드백 후 수정하고 싶은 내용은?")
        thought_change = st.text_area("AI 피드백을 읽고 난 후, 자신의 보고서 중 수정할 부분과 AI 피드백에 대한 자신의 생각을 작성해 주세요.", height=150, key="thought_change")
        submit_thought = st.form_submit_button("피드백 수정 및 느낀점 제출하기")

        if submit_thought:
            # student_id, student_name을 session_state에서 불러와서 전달
            update_thought_change(
                st.session_state.get("student_id", ""),
                st.session_state.get("student_name", ""),
                thought_change
            )
            st.success("수고했습니다. 피드백 및 느낀점 제출 완료!")
            st.session_state["ai_feedback"] = ""  # 제출 후 리셋

# 제출된 보고서 목록
st.markdown("---")
with st.expander("📄 제출된 보고서 목록 보기", expanded=False):
    reports = get_reports()
    if reports:
        for r in reports[:10]:
            ctime = r["created_at"][:16] if r.get("created_at") else ""
            sid = r.get("student_id", "")
            sname = r.get("student_name", "")
            s_report = r.get("student_report", "")
            ai_feed = r.get("ai_feedback", "")
            t_change = r.get("thought_change", "")
            st.markdown(f"""
            - **[{ctime}] {sid} {sname}**
                - **보고서 요약:** {s_report[:80]}...
                - **AI 피드백:** {ai_feed[:80]}...
                - **피드백 후 느낀점:** {t_change[:80] if t_change else "(작성 전)"}...
            """)
    else:
        st.info("제출된 보고서가 없습니다.")