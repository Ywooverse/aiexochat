import streamlit as st
import openai
import time
import random
import threading
from supabase import create_client, Client

# ✅ 1. 보안 정보 로딩
OPENAI_API_KEY = st.secrets["openai"]["api_key"]
ASSISTANT_ID = st.secrets["openai"]["assistant_id"]
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

client = openai.OpenAI(api_key=OPENAI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ 2. 페이지 설정
st.set_page_config(page_title="외계 행성 탐사 도우미", page_icon="🤖", layout="centered")
st.header("🤖 인공지능과 아두이노를 활용한 외계 행성 탐사 도우미")

# ✅ 3. 사용자 이름 입력
if "student_name" not in st.session_state:
    st.session_state.student_name = ""

student_name = st.text_input("학생 이름을 입력하세요:", value=st.session_state.student_name, max_chars=20)
if student_name:
    st.session_state.student_name = student_name

if not st.session_state.student_name:
    st.info("이름을 먼저 입력하세요.")
    st.stop()

# ✅ 4. 대화 세션 & 버퍼 초기화
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

if "chat_buffer" not in st.session_state:
    st.session_state.chat_buffer = []

if "save_scheduled" not in st.session_state:
    st.session_state.save_scheduled = False

thread_id = st.session_state.thread_id

# ✅ 5. 이전 대화 불러오기
thread_messages = client.beta.threads.messages.list(thread_id, order="asc")
for msg in thread_messages.data:
    with st.chat_message(msg.role):
        st.write(msg.content[0].text.value)

# ✅ 6. 랜덤 저장 예약 함수
def schedule_random_save():
    if not st.session_state.save_scheduled:
        delay = random.randint(10, 60)  # 10~60초
        threading.Timer(delay, save_chat_history).start()
        st.session_state.save_scheduled = True

# ✅ 7. Supabase 저장 함수
def save_chat_history():
    if not st.session_state.chat_buffer:
        st.session_state.save_scheduled = False
        return  # 저장할 것이 없으면 중단

    for chat in st.session_state.chat_buffer:
        try:
            supabase.table("chat_history").insert({
                "student_name": st.session_state.student_name,
                "question": chat["q"],
                "answer": chat["a"]
            }).execute()
        except Exception as e:
            print("❗ Supabase 저장 실패:", e)

    st.session_state.chat_buffer = []         # 버퍼 비우기
    st.session_state.save_scheduled = False   # 다음 예약 가능하도록 초기화

# ✅ 8. 사용자 질문 입력 처리
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

    # ✅ 질문/답변을 버퍼에 저장
    st.session_state.chat_buffer.append({
        "q": prompt,
        "a": answer
    })

    # ✅ 랜덤 저장 예약
    schedule_random_save()

# ✅ 9. 수동 저장 버튼 (예: 수업 종료 전)
if st.button("💾 지금까지 질문 저장하기"):
    save_chat_history()
    st.success("모든 질문/답변이 저장되었습니다.")