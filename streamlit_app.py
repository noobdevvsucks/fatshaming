import streamlit as st
import os
import google.generativeai as genai

# Set page config
st.set_page_config(page_title="Personalized Fitness Assistant")

# Handle Gemini API key
if 'GEMINI_API_KEY' in st.secrets:
    gemini_api_key = st.secrets['GEMINI_API_KEY']
else:
    gemini_api_key = st.text_input("Enter Gemini API key:", type="password")

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

# Session state for page navigation
if "page" not in st.session_state:
    st.session_state.page = "form"

# Step 1: User Input Form
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
        bmi = weight / (height ** 2)

        # Fitness score logic
        def calculate_fitness_score(user_data):
            score = 0
            age = user_data["age"]
            bmi = user_data["bmi"]

            if age <= 30:
                score += 15
            elif age <= 45:
                score += 10
            elif age <= 60:
                score += 5
            else:
                score += 2

            if 18.5 <= bmi <= 24.9:
                score += 15
            else:
                score += 5

            eq_map = {
                "None": 0,
                "Some (e.g. dumbbells, bands)": 10,
                "Full gym access": 20
            }
            score += eq_map.get(user_data["equipment"], 0)
            return score

        user_data = {
            "weight": weight,
            "height": height,
            "age": age,
            "gender": gender,
            "days_free": days_free,
            "bmi": bmi,
            "experience": experience,
            "duration": duration,
            "equipment": equipment,
        }

        fitness_score = calculate_fitness_score(user_data)
        user_data["fitness_score"] = fitness_score

        st.session_state.user_data = user_data
        st.session_state.page = "chat"
        st.rerun()

# Step 2: Chatbot Page
elif st.session_state.page == "chat":
    st.title("Personalized Fitness Chatbot 💬")

    user = st.session_state.user_data

    st.write(f"**BMI**: {round(user['bmi'], 2)}")
    st.write(f"**Fitness Score**: {user['fitness_score']}/80")
    st.write(f"**Free Days**: {', '.join(user['days_free'])}")

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "fitness instructor",
            "content": "Hi! I'm your fitness coach. How can I help you reach your goals today?"
        }]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Function to generate Gemini response
    def generate_gemini_response(user_input, user):
        prompt = (
            f"You are a friendly and professional fitness instructor.\n"
            f"User details:\n"
            f"- Age: {user['age']} years\n"
            f"- BMI: {round(user['bmi'], 2)}\n"
            f"- Experience: {user['experience']}\n"
            f"- Duration: {user['duration']} minutes per session\n"
            f"- Free Days: {', '.join(user['days_free'])}\n"
            f"- Equipment: {user['equipment']}\n"
            f"- Fitness Score: {user['fitness_score']}/80\n\n"
            f"User's question: {user_input}\n\n"
            f"Respond in a supportive, motivating tone. Be specific and actionable."
        )

        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            st.error(f"Gemini API Error: {e}")
            return "Sorry, I couldn't generate a response. Please try again later."

    if prompt := st.chat_input("Ask me anything about your fitness plan!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("fitness instructor"):
            with st.spinner("Generating response..."):
                reply = generate_gemini_response(prompt, user)
                st.write(reply)
                st.session_state.messages.append({"role": "fitness instructor", "content": reply})
