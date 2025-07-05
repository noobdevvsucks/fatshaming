import streamlit as st
import replicate
import os

st.set_page_config(page_title="Fitness Schedule")

DAYS_FREE_OPTIONS = ["Sunday Morning", "Sunday Evening", "Monday Morning", "Monday Evening", "Tuesday Morning", "Tuesday Evening", "Wednesday Morning", "Wednesday Evening", "Thursday Morning", "Thursday Evening", "Friday Morning", "Friday Evening", "Saturday Morning", "Saturday Evening"]

if "page" not in st.session_state:
    st.session_state.page = "form"

if st.session_state.page == "form":
    st.title("Personal Fitness Setup")
    with st.form("user_info_form"):
        weight = st.number_input("Weight (kg):", min_value=1.0, step=0.1)
        height = st.number_input("Height (m):", min_value=0.5, step=0.01)
        age = st.number_input("Age:", min_value=1)
        gender = st.selectbox("Gender:", ["Male", "Female", "Other"])
        sleep_time = st.slider("Sleep Time (hours):", 0.0, 24.0, 8.0, 0.5)
        days_free = st.multiselect("Days You're Free:", DAYS_FREE_OPTIONS)
        complete = st.form_submit_button("Complete")
    if complete:
        st.session_state.user_data = {
            "weight": weight,
            "height": height,
            "age": age,
            "gender": gender,
            "sleep_time": sleep_time,
            "days_free": days_free,
            "bmi": weight / (height ** 2)
        }
        st.session_state.page = "chat"
        st.experimental_rerun()

elif st.session_state.page == "chat":
    st.title("Fitness Chatbot 💬")
    with st.sidebar:
        if 'REPLICATE_API_TOKEN' in st.secrets:
            st.success('API key already provided!', icon='✅')
            replicate_api = st.secrets['REPLICATE_API_TOKEN']
        else:
            replicate_api = st.text_input('Enter Replicate API token:', type='password')
        os.environ['REPLICATE_API_TOKEN'] = replicate_api
        st.write("BMI:", round(st.session_state.user_data["bmi"], 2))
        st.write("Free Days:", ", ".join(st.session_state.user_data["days_free"]))
        st.button('Back to Form', on_click=lambda: st.session_state.update({"page": "form"}))

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "fitness instructor",
            "content": "Hi! Based on your profile, how can I help you with your fitness goals today?"
        }]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    def generate_llama2_response(prompt_input):
        base_prompt = (
            "You are a fitness instructor. Use the following user data: "
            f"Weight: {st.session_state.user_data['weight']} kg, "
            f"Height: {st.session_state.user_data['height']} m, "
            f"Age: {st.session_state.user_data['age']}, "
            f"Gender: {st.session_state.user_data['gender']}, "
            f"Sleep Time: {st.session_state.user_data['sleep_time']} hrs, "
            f"Free Days: {', '.join(st.session_state.user_data['days_free'])}. "
            "Create schedules, give advice, and ask for more goals."
        )
        chat_history = base_prompt
        for msg in st.session_state.messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            chat_history += f"\n{role}: {msg['content']}"
        response = replicate.run(
            "a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5",
            input={"prompt": f"{chat_history}\nAssistant:", "temperature": 0.1, "top_p": 0.9, "max_length": 100, "repetition_penalty": 1}
        )
        return ''.join(response)

    if prompt := st.chat_input("Ask me anything!", disabled=not replicate_api):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("fitness instructor"):
            with st.spinner("Thinking..."):
                reply = generate_llama2_response(prompt)
                st.write(reply)
                st.session_state.messages.append({"role": "fitness instructor", "content": reply})
