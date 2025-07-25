import streamlit as st
import replicate
import os

# Set up Replicate API Token
if 'REPLICATE_API_TOKEN' in st.secrets:
    replicate_api = st.secrets['REPLICATE_API_TOKEN']
else:
    replicate_api = st.text_input('Enter Replicate API token:', type='password')

if not replicate_api:
    st.warning("Please enter your Replicate API token to continue.")
    st.stop()

os.environ['REPLICATE_API_TOKEN'] = replicate_api

# Streamlit page configuration
st.set_page_config(page_title="Personalized Fitness Assistant")

# Session state for page navigation
if "page" not in st.session_state:
    st.session_state.page = "form"

# Step 1: Personal Info Form
if st.session_state.page == "form":
    st.title("Create Your Fitness Profile")

    with st.form("user_info_form"):
        weight = st.number_input("Weight (kg):", min_value=1.0, step=0.1)
        height = st.number_input("Height (m):", min_value=0.5, step=0.01)
        age = st.number_input("Age:", min_value=1)
        gender = st.selectbox("Gender:", ["Male", "Female", "Other"])
        days_free = st.multiselect("Days You're Free:", ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
        experience = st.selectbox("Fitness Experience:", ["Beginner", "Intermediate", "Advanced"])
        duration = st.slider("Typical Workout Duration (minutes):", 10, 90, 30, 5)
        equipment = st.selectbox("Available Equipment:", ["None", "Some (e.g. dumbbells, bands)", "Full gym access"])
        complete = st.form_submit_button("Complete")

    if complete:
        st.session_state.user_data = {
            "weight": weight,
            "height": height,
            "age": age,
            "gender": gender,
            "days_free": days_free,
            "bmi": (weight / (height ** 2)),
            "experience": experience,
            "duration": duration,
            "equipment": equipment,
        }
        st.session_state.page = "chat"
        st.rerun()

# Fitness Score Mapping
eq_map = {
    "None": 5,
    "Some (e.g. dumbbells, bands)": 10,
    "Full gym access": 15
}

def calculate_fitness_score(user_data):
    score = 0
    age = user_data["age"]
    bmi = user_data["bmi"]

    # Age scoring
    if age <= 30:
        score += 15
    elif age <= 45:
        score += 10
    elif age <= 60:
        score += 5
    else:
        score += 2

    # BMI scoring
    if 18.5 <= bmi <= 24.9:
        score += 15
    else:
        score += 5

    # Equipment scoring
    score += eq_map.get(user_data["equipment"], 0)

    return score

# Calculate fitness score only once
if "user_data" in st.session_state and "fitness_score" not in st.session_state.user_data:
    st.session_state.user_data["fitness_score"] = calculate_fitness_score(st.session_state.user_data)

# Step 2: Chatbot Page
if st.session_state.page == "chat":
    st.title("Personalized Fitness Chatbot 💬")

    user = st.session_state.user_data
    st.write(f"**BMI**: {round(user['bmi'], 2)}")
    st.write(f"**Free Days**: {', '.join(user['days_free'])}")
    st.write(f"**Fitness Score**: {user['fitness_score']}/80")

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "fitness instructor",
            "content": "Hi! How can I assist you with your fitness journey today?"
        }]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    def generate_llama_response(prompt_input):
        user = st.session_state.user_data
        user_input = prompt_input
        context = (
            f"The user is {user['age']} years old with a BMI of {round(user['bmi'], 2)}.\n"
            f"They have {user['experience']} fitness experience, typically work out for {user['duration']} minutes, "
            f"and are free on {', '.join(user['days_free'])}.\n"
            f"Fitness Score: {user['fitness_score']}/80.\n\n"
            f"Time per workout: {user['duration']}\n"
            f"Equipment open to user: {user['equipment']}\n"
            f"User's question: {user_input}\n\nRespond as a friendly fitness coach."
        )
        try:
            response = replicate.run(
                "a16z-infra/llama2-v2-chat:latest",
                input={"prompt": context + "\nAssistant:", "temperature": 0.7, "max_length": 150}
            )
            return ''.join(response)
        except replicate.exceptions.ReplicateError as e:
            st.error(f"Error: {e}")
            return "Sorry, there was an error processing your request. Please try again later."

    if prompt := st.chat_input("Ask me anything about your fitness plan!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("fitness instructor"):
            with st.spinner("Thinking..."):
                reply = generate_llama_response(prompt)
                st.write(rep
