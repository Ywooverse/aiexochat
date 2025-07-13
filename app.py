import streamlit as st
import openai
import time
from supabase import create_client, Client

# 1. 보안 정보 로딩
OPENAI_API_KEY = st.secrets["openai"]["api_key"]
ASSISTANT_ID = st.secrets["openai"]["assistant_id"]
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

client = openai.OpenAI(api_key=OPENAI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. 페이지 설정
st.set_page_config(page_title="외계 행성 탐사 도우미", page_icon="🤖", layout="centered")
st.header("🤖 인공지능과 아두이노를 활용한 외계 행성 탐사 도우미")

# 3. 세션 상태 초기화
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "student_name_entered" not in st.session_state:
    st.session_state.student_name_entered = False
if "chat_buffer" not in st.session_state:
    st.session_state.chat_buffer = []
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

thread_id = st.session_state.thread_id

# 4. 학생 이름 입력 UI (입력창과 전송 버튼 한 줄)
if not st.session_state.student_name_entered:
    error_msg = None
    with st.form(key="name_form", clear_on_submit=False):
        col1, col2 = st.columns([4, 1])
        with col1:
            student_name = st.text_input(
                "",
                value=st.session_state.student_name,
                key="name_input",
                max_chars=20,
                placeholder="이름을 입력하세요",
                label_visibility="collapsed"
            )
        with col2:
            submitted = st.form_submit_button("전송")
        if submitted:
            if student_name.strip() != "":
                st.session_state.student_name = student_name.strip()
                st.session_state.student_name_entered = True
                st.rerun()
            else:
                error_msg = "⚠️ 반드시 이름을 입력한 후 전송하세요!"
    if error_msg:
        st.error(error_msg)
    st.stop()
else:
    st.success(f"👤 학생 이름: {st.session_state.student_name}")

# 5. 이전 대화 표시
thread_messages = client.beta.threads.messages.list(thread_id, order="asc")
for msg in thread_messages.data:
    with st.chat_message(msg.role):
        st.write(msg.content[0].text.value)

# 6. 사용자 질문 입력 처리 및 저장(실패시 버퍼에 저장)
prompt = st.chat_input("질문을 입력하세요!")
if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=prompt
    )
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID,
    )
    with st.spinner("🤖 답변 생성 중..."):
        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
    messages = client.beta.threads.messages.list(thread_id=thread_id, order="desc")
    answer = None
    for msg in messages.data:
        if msg.role == "assistant":
            answer = msg.content[0].text.value
            with st.chat_message("assistant"):
                st.write(answer)
            break
    # 바로 Supabase 저장 시도
    try:
        supabase.table("chat_history").insert({
            "student_name": st.session_state.student_name,
            "question": prompt,
            "answer": answer
        }).execute()
    except Exception as e:
        st.warning("⚠️ 저장에 실패했습니다. 나중에 '질문 저장하기' 버튼을 눌러 재시도하세요.")
        st.session_state.chat_buffer.append({
            "q": prompt,
            "a": answer
        })

# 7. 버퍼에 남은 데이터 있을 때만 저장 버튼 노출 & 재시도 기능
if st.session_state.chat_buffer:
    if st.button("💾 질문 저장하기 (저장 실패시 재시도)"):
        failed = False
        for chat in st.session_state.chat_buffer[:]:
            try:
                supabase.table("chat_history").insert({
                    "student_name": st.session_state.student_name,
                    "question": chat["q"],
                    "answer": chat["a"]
                }).execute()
                st.session_state.chat_buffer.remove(chat)
            except Exception as e:
                failed = True
                st.warning(f"⚠️ 일부 저장 실패: {e}")
        if not failed:
            st.success("모든 질문/답변이 저장되었습니다.")
        elif not st.session_state.chat_buffer:
            st.success("모든 질문/답변이 저장되었습니다.")