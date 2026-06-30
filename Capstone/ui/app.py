"""Streamlit UI for the Multi-Agent Day Planner. Run: streamlit run streamlit_app/app.py"""
import streamlit as st
import httpx
import pandas as pd

API_BASE = "http://127.0.0.1:8000"
st.set_page_config(page_title="AI Day Planner", page_icon="🧠", layout="wide")
st.markdown("""
<style>

/* Generate Day Plan Button */
div.stButton > button:first-child {
    background: linear-gradient(90deg, #2563eb, #3b82f6);
    color: white;
    border-radius: 12px;
    border: none;
    padding: 0.6rem 1.5rem;
    font-size: 18px;
    font-weight: 600;
    transition: 0.3s;
}

/* Hover Effect */
div.stButton > button:first-child:hover {
    background: linear-gradient(90deg, #1d4ed8, #2563eb);
    transform: scale(1.03);
    box-shadow: 0px 8px 20px rgba(37,99,235,0.35);
}

/* Click Effect */
div.stButton > button:first-child:active {
    transform: scale(0.98);
}

</style>
""", unsafe_allow_html=True)

def api_post(path, payload):
    try:
        r = httpx.post(f"{API_BASE}{path}", json=payload, timeout=90)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        st.error(f"Connection error: {e}")
    return {}


def api_get(path, params=None):
    try:
        r = httpx.get(f"{API_BASE}{path}", params=params or {}, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Error: {e}")
    return {}


# for key, value in {"logged_in": False, "user": None, "auth_page": "signup", "latest_plan_id": None}.items():
#     if key not in st.session_state:
#         st.session_state[key] = value

# if st.sidebar.button("Reset App / Logout"):
#     st.session_state.logged_in = False
#     st.session_state.user = None
#     st.session_state.auth_page = "signup"
#     st.rerun()


# Initialize session state
defaults = {
    "logged_in": False,
    "user": None,
    "auth_page": "signup",
    "latest_plan_id": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Reset application
if st.sidebar.button("🔄 Reset App / Logout"):
    for key, value in defaults.items():
        st.session_state[key] = value

    st.cache_data.clear()
    st.cache_resource.clear()

    st.rerun()


def signup_page():
    st.title("🆕 New User Signup")
    st.caption("Create your health and lifestyle profile.")
    with st.form("signup_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        email = c2.text_input("Email ID")
        phone = c1.text_input("Phone Number", placeholder="+91XXXXXXXXXX")
        profession = c2.text_input("Profession")
        password = c1.text_input("Password", type="password")
        confirm_password = c2.text_input("Confirm Password", type="password")
        c3, c4, c5 = st.columns(3)
        height = c3.number_input("Height (cm)", 50.0, 250.0, 170.0)
        weight = c4.number_input("Weight (kg)", 20.0, 200.0, 70.0)
        age = c5.number_input("Age", 10, 100, 25)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        diseases = st.multiselect("Diseases", ["None", "BP", "Sugar", "Heart", "Asthma", "Thyroid"])
        disability = st.text_input("Disability, if any", placeholder="Write None if not applicable")
        submitted = st.form_submit_button("Signup", type="primary", use_container_width=True)
    if submitted:
        if password != confirm_password:
            st.error("Password and confirm password do not match.")
            return
        if not name or not email or not password:
            st.error("Please fill Name, Email and Password.")
            return
        result = api_post("/auth/signup", {"name": name, "email": email, "phone": phone, "password": password, "height": height, "weight": weight, "gender": gender, "age": int(age), "profession": profession, "diseases": diseases, "disability": disability})
        if result.get("user"):
            st.success("Signup successful. Please login.")
            st.session_state.auth_page = "login"
            st.rerun()
    st.divider()
    if st.button("Already have an account? Login"):
        st.session_state.auth_page = "login"
        st.rerun()


def login_page():
    st.title("🔐 Login")
    st.caption("For demo, email login is enabled. In production, password should always be required.")
    email = st.text_input("Email ID")
    password = st.text_input("Password Optional", type="password")
    if st.button("Login", type="primary", use_container_width=True):
        result = api_post("/auth/login", {"email": email, "password": password if password else None})
        if result.get("user"):
            st.session_state.logged_in = True
            st.session_state.user = result["user"]
            st.success("Login successful.")
            st.rerun()
    st.divider()
    if st.button("New user? Signup"):
        st.session_state.auth_page = "signup"
        st.rerun()


if not st.session_state.logged_in:
    signup_page() if st.session_state.auth_page == "signup" else login_page()
    st.stop()

user = st.session_state.user
with st.sidebar:
    st.title("🧠 AI Day Planner")
    st.caption("Multi-Agent • Indian Meals • SMS Optional")
    st.divider()
    st.write(f"Logged in as: **{user['name']}**")
    st.caption(user["email"])
    page = st.radio("Navigate", ["📅 Day Planner", "👤 Profile", "📜 History", "💬 Feedback", "📊 Analytics"], label_visibility="collapsed")
    st.divider()
    phone = st.text_input("Phone Optional", value=user.get("phone") or "")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.auth_page = "login"
        st.session_state.latest_plan_id = None
        st.rerun()

#if page == "📅 Day Planner":
    # st.title("📅 Generate My Day Plan")
    # st.caption("Agent 1 creates the plan, Agent 2 analyses history, Agent 3 adds safety/fallback suggestions.")
    # c1, c2 = st.columns(2)
    # wake_time = c1.time_input("Wake-up time")
    # sleep_time = c2.time_input("Sleep time")
    # diet_type = st.selectbox("Diet Preference", ["Veg", "Non-Veg"])
    # fitness_type = st.selectbox("Fitness Preference", ["Gym", "Yoga", "Both"])
    # workout_duration = st.selectbox("Workout Duration", ["1 hr", "1.5 hr", "2 hr"])
    # preferences_text = st.text_area("Extra Preferences", placeholder="Example: office 9 to 6, avoid rice at night, evening gym")
    # if st.button("✨ Generate My Day Plan", type="primary", use_container_width=True):
    #     with st.spinner("Multi-agent system is generating your plan..."):
    #         result = api_post("/planner/generate", {"user_id": user["id"], "wake_time": wake_time.strftime("%H:%M"), "sleep_time": sleep_time.strftime("%H:%M"), "diet_type": diet_type, "fitness_type": fitness_type, "workout_duration": workout_duration, "phone": phone or None, "preferences": {"notes": preferences_text}})
    #     if result.get("events"):
    #         st.session_state.latest_plan_id = result.get("plan_id")
    #         st.success("Day plan generated successfully.")
    #         st.subheader("Your Day Plan")
    #         st.dataframe(pd.DataFrame(result["events"]), use_container_width=True)
    #         st.subheader("Agent Output")
    #         st.json(result.get("agent_analysis", {}))
    #         st.subheader("Notification")
    #         st.json(result.get("notification", {}))

# if page == "📅 Day Planner":
#     st.title("📅 Generate My Day Plan")
#     st.caption("Agent 1 creates the plan. Validator checks wake/sleep constraint. User can edit and update plan.")

#     c1, c2 = st.columns(2)
#     wake_time = c1.time_input("Wake-up time")
#     sleep_time = c2.time_input("Sleep time")

#     diet_type = st.selectbox("Diet Preference", ["Veg", "Non-Veg"])
#     fitness_type = st.selectbox("Fitness Preference", ["Gym", "Yoga", "Both"])
#     workout_duration = st.selectbox("Workout Duration", ["1 hr", "1.5 hr", "2 hr"])

#     preferences_text = st.text_area(
#         "Extra Preferences",
#         placeholder="Example: office 9 to 6, avoid rice at night, evening gym"
#     )

#     wake_str = wake_time.strftime("%H:%M")
#     sleep_str = sleep_time.strftime("%H:%M")

#     if "current_events" not in st.session_state:
#         st.session_state.current_events = []

#     if st.button("✨ Generate My Day Plan", type="primary", use_container_width=True):
#         with st.spinner("Multi-agent system is generating your plan..."):
#             result = api_post(
#                 "/planner/generate",
#                 {
#                     "user_id": user["id"],
#                     "wake_time": wake_str,
#                     "sleep_time": sleep_str,
#                     "diet_type": diet_type,
#                     "fitness_type": fitness_type,
#                     "workout_duration": workout_duration,
#                     "phone": phone or None,
#                     "preferences": {
#                         "notes": preferences_text
#                     }
#                 }
#             )

#         if result.get("events"):
#             st.session_state.latest_plan_id = result.get("plan_id")
#             st.session_state.current_events = result["events"]

#             st.success("Day plan generated successfully.")

#             if result.get("validation_errors"):
#                 st.warning("Some validation warnings found:")
#                 st.write(result["validation_errors"])

#             #st.subheader("Agent Output")
#             #st.json(result.get("agent_analysis", {}))
# #
#             #st.subheader("Notification")
#             #st.json(result.get("notification", {}))

#     if st.session_state.current_events:
#         st.subheader("Your Editable Day Plan")

#         df = pd.DataFrame(st.session_state.current_events)

#         edited_df = st.data_editor(
#             df,
#             use_container_width=True,
#             num_rows="dynamic",
#             key="editable_day_plan"
#         )

#         if st.button("🔄 Update My Day Plan", use_container_width=True):
#             updated_events = edited_df.to_dict("records")

#             with st.spinner("Updating your day plan..."):
#                 update_result = api_post(
#                     "/planner/update",
#                     {
#                         "user_id": user["id"],
#                         "plan_id": st.session_state.latest_plan_id,
#                         "wake_time": wake_str,
#                         "sleep_time": sleep_str,
#                         "diet_type": diet_type,
#                         "fitness_type": fitness_type,
#                         "workout_duration": workout_duration,
#                         "events": updated_events
#                     }
#                 )

#             if update_result.get("events"):
#                 st.session_state.current_events = update_result["events"]
#                 st.success("Day plan updated successfully.")

#                 if update_result.get("validation_errors"):
#                     st.warning("Validation warnings:")
#                     st.write(update_result["validation_errors"])

#                 st.subheader("Updated Plan")
#                 st.dataframe(
#                     pd.DataFrame(update_result["events"]),
#                     use_container_width=True
#                 )

if page == "📅 Day Planner":
    st.title("📅 Generate My Day Plan")
    st.caption("Agent 1 creates, Agent 2 finalises, Agent 3 validates.")

    c1, c2 = st.columns(2)
    wake_time = c1.time_input("Wake-up time")
    sleep_time = c2.time_input("Sleep time")

    # office_time = st.text_input(
    #     "Office / Work Time",
    #     placeholder="Example: I am in office 9 AM to 7 PM"
    # )

    st.subheader("🏢 Work Schedule")

    c1, c2 = st.columns(2)

    office_start = c1.time_input(
        "Office Start Time",
        value=None,
        key="office_start"
    )

    office_end = c2.time_input(
        "Office End Time",
        value=None,
        key="office_end"
    )

    work_mode = st.selectbox(
        "Work Mode",
        [
            "Office",
            "Work From Home",
            "Hybrid",
            "Student",
            "Not Working"
        ]
    )

    gym_preference = st.selectbox(
        "Workout Timing",
        [
            "Morning",
            "After Office",
            "Evening",
            "Flexible"
        ]
    )

    diet_type = st.selectbox("Diet Preference", ["Veg", "Non-Veg"])
    fitness_type = st.selectbox("Fitness Preference", ["Gym", "Yoga", "Both"])
    workout_duration = st.selectbox("Workout Duration", ["1 hr", "1.5 hr", "2 hr"])

    preferences_text = st.text_area(
        "Extra Preferences",
        placeholder="Example: avoid rice at night, gym after office, light dinner"
    )

    wake_str = wake_time.strftime("%H:%M")
    sleep_str = sleep_time.strftime("%H:%M")

    if "current_events" not in st.session_state:
        st.session_state.current_events = []

    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False

    if st.button("✨ Generate My Day Plan", type="primary", use_container_width=True):
        # result = api_post(
        #     "/planner/generate",
            # {
            #     "user_id": user["id"],
            #     "wake_time": wake_str,
            #     "sleep_time": sleep_str,
            #     "diet_type": diet_type,
            #     "fitness_type": fitness_type,
            #     "workout_duration": workout_duration,
            #     "phone": phone or None,
            #     "preferences": {
            #         "notes": preferences_text,
            #         "office_time": office_time
            #     }
            # }

        # )
        result = api_post(
            "/planner/generate",
            {
                "user_id": user["id"],
                "wake_time": wake_str,
                "sleep_time": sleep_str,
                "diet_type": diet_type,
                "fitness_type": fitness_type,
                "workout_duration": workout_duration,
                "phone": phone or None,
                "preferences": {
                    "notes": preferences_text,
                    "work_mode": work_mode,
                    "office_start": office_start.strftime("%H:%M") if office_start else None,
                    "office_end": office_end.strftime("%H:%M") if office_end else None,
                    "gym_preference": gym_preference
                }
            }
        )

        if result.get("events"):
            st.session_state.latest_plan_id = result.get("plan_id")
            st.session_state.current_events = result["events"]
            st.session_state.edit_mode = False
            st.success("Day plan generated successfully.")

            if result.get("validation"):
                st.json(result["validation"])

    if st.session_state.current_events:
        st.subheader("Your Day Plan")

        if not st.session_state.edit_mode:
            st.dataframe(
                pd.DataFrame(st.session_state.current_events),
                use_container_width=True
            )

            if st.button("✏️ Edit Day Plan", use_container_width=True):
                st.session_state.edit_mode = True
                st.rerun()

        else:
            st.info("Edit time/activity based on what actually happened or what you want to change.")

            edited_df = st.data_editor(
                pd.DataFrame(st.session_state.current_events),
                use_container_width=True,
                num_rows="dynamic",
                key="editable_day_plan"
            )

            user_change_reason = st.text_area(
                "What changed?",
                placeholder="Example: I did not have grilled chicken. I had rice and dal. Also lunch happened at 2 PM because of office work."
            )

            c1, c2 = st.columns(2)

            if c1.button("✅ Finalise Updated Plan", use_container_width=True):
                result = api_post(
                    "/planner/finalize",
                    {
                        "user_id": user["id"],
                        "plan_id": st.session_state.latest_plan_id,
                        "wake_time": wake_str,
                        "sleep_time": sleep_str,
                        "diet_type": diet_type,
                        "fitness_type": fitness_type,
                        "workout_duration": workout_duration,
                        "events": edited_df.to_dict("records"),
                        "preferences": {
                            "notes": preferences_text,
                            "office_time": office_time,
                            "user_change_reason": user_change_reason
                        }
                    }
                )

                if result.get("events"):
                    st.session_state.current_events = result["events"]
                    st.session_state.latest_plan_id = result.get("new_plan_id")
                    st.session_state.edit_mode = False
                    st.success("Updated day plan finalised successfully.")

                    if result.get("validation"):
                        st.json(result["validation"])

                    st.rerun()

            if c2.button("❌ Cancel Edit", use_container_width=True):
                st.session_state.edit_mode = False
                st.rerun()

elif page == "👤 Profile":
    st.title("👤 Edit Profile")
    st.caption("Update your health and lifestyle profile. Future day plans will use this updated data.")

    current_diseases = user.get("diseases") or ""
    current_diseases_list = [
        d.strip() for d in current_diseases.split(",") if d.strip()
    ]

    with st.form("profile_update_form"):
        c1, c2 = st.columns(2)

        phone_new = c1.text_input("Phone Number", value=user.get("phone") or "")
        profession_new = c2.text_input("Profession", value=user.get("profession") or "")

        height_new = c1.number_input(
            "Height (cm)",
            50.0,
            250.0,
            float(user.get("height") or 170.0),
        )

        weight_new = c2.number_input(
            "Weight (kg)",
            20.0,
            200.0,
            float(user.get("weight") or 70.0),
        )

        age_new = c1.number_input(
            "Age",
            10,
            100,
            int(user.get("age") or 25),
        )

        diseases_new = st.multiselect(
            "Diseases",
            ["None", "BP", "Sugar", "Heart", "Asthma", "Thyroid"],
            default=current_diseases_list if current_diseases_list else ["None"],
        )

        disability_new = st.text_input(
            "Disability, if any",
            value=user.get("disability") or "",
        )

        submitted = st.form_submit_button(
            "💾 Update Profile",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        result = api_post(
            "/profile/update",
            {
                "user_id": user["id"],
                "phone": phone_new,
                "height": height_new,
                "weight": weight_new,
                "age": int(age_new),
                "profession": profession_new,
                "diseases": diseases_new,
                "disability": disability_new,
            },
        )

        if result.get("user"):
            st.session_state.user = result["user"]
            st.success("Profile updated successfully.")
            st.rerun()
elif page == "📜 History":
    st.title("📜 Day Plan History")
    limit = st.slider("Show last N plans", 1, 20, 5)
    if st.button("Load History", use_container_width=True):
        result = api_get(f"/history/{user['id']}", {"limit": limit})
        entries = result.get("entries", [])
        if not entries:
            st.info("No history found.")
        for item in entries:
            with st.expander(f"Plan #{item['id']} | {item['created_at']}"):
                st.write(f"Diet: **{item['diet_type']}**, Fitness: **{item['fitness_type']}**, Workout: **{item['workout_duration']}**")
                st.dataframe(pd.DataFrame(item["events"]), use_container_width=True)
                st.json(item["analysis"])
elif page == "💬 Feedback":
    st.title("💬 User Feedback")
    if not st.session_state.latest_plan_id:
        st.info("Generate a day plan first, then submit feedback.")
    else:
        rating = st.slider("Rating", 1, 5, 4)
        comments = st.text_area("Comments")
        if st.button("Submit Feedback", type="primary", use_container_width=True):
            result = api_post("/feedback", {"user_id": user["id"], "plan_id": st.session_state.latest_plan_id, "rating": rating, "comments": comments})
            if result.get("message"):
                st.success(result["message"])
elif page == "📊 Analytics":
    st.title("📊 Analytics / Observability")
    st.info("For MVP, this page shows API links. Prometheus/Grafana can be added later.")
    st.markdown("""
| Service | URL |
|---|---|
| FastAPI Docs | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| API Health | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) |
""")
