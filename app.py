import streamlit as st
import pandas as pd
from utils.cache_functions import load_nursing_data, skills_overlap, specialty_compensation, average_pay_model
from utils.llm_functions import generate_nurse_summary_for_user, generate_culture_summary_from_inputs, compute_skill_transfer_options, refine_skill_transfer_bullets

st.set_page_config(page_title="Nurse AI Summary Tester", layout="wide")

# ----------------------
# Load and Prepare Data
# ----------------------
nursing_df = load_nursing_data()
skills_overlap_df = skills_overlap()
specialty_comp_df = specialty_compensation()
average_pay_df = average_pay_model()

# Define important fields for summary quality
important_fields = [
    'nursing_role', 'specialty', 'hospital', 'city', 'state',
    'base_pay', 'shift_type', 'employment_type', 'differentials',
    'general_feedback', 'total_years_of_experience'
]

# Calculate completeness score per row
nursing_df['completeness_score'] = nursing_df[important_fields].notnull().mean(axis=1)

# Get max completeness score per user
user_completeness = nursing_df.groupby('user_id')['completeness_score'].max().reset_index()
user_completeness.columns = ['user_id', 'completeness_score_user_max']

# Merge back to original dataframe
nursing_df = nursing_df.merge(user_completeness, on='user_id', how='left')

# ----------------------
# UI Setup
# ----------------------
st.title("🧠 AI Insights for Nurses")

# ----------------------
# Sidebar Filters
# ----------------------
st.sidebar.header("👤 Select User and Filters")

# Specialty filter
specialty_options = ["All"] + sorted(nursing_df['specialty'].dropna().unique().tolist())
selected_specialty = st.sidebar.selectbox("Filter by Specialty", specialty_options)

# Location filter (by state)
location_options = ["All"] + sorted(nursing_df['state'].dropna().unique())
selected_location = st.sidebar.selectbox("Filter by Location", location_options)

# Filter for aggregate and cohort-level analysis
filtered_df = nursing_df.copy()
if selected_specialty != "All":
    filtered_df = filtered_df[filtered_df["specialty"] == selected_specialty]
if selected_location != "All":
    filtered_df = filtered_df[filtered_df["state"] == selected_location]

# Filter for selecting clean user examples only
example_df = filtered_df[filtered_df['completeness_score_user_max'] >= 0.7]
example_user_ids = example_df['user_id'].dropna().unique().tolist()

if not example_user_ids:
    st.sidebar.warning("⚠️ No users found with enough data in this filter combination.")
    st.stop()

selected_user = st.sidebar.selectbox("Select a User ID", example_user_ids)

# Show current filters
st.markdown(f"##### 🧪 Viewing: **Specialty:** `{selected_specialty}` | **Location:** `{selected_location}`")

st.markdown("---")

# Show raw user rows (all jobs, full info)
user_rows = nursing_df[nursing_df['user_id'] == selected_user]
st.markdown("### 📄 Selected User: Full Row View")
st.dataframe(user_rows, use_container_width=True)

st.markdown("---")

# ----------------------
# Main Tabs
# ----------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🧑‍⚕️ Summary",
    "🌱 Culture",
    "🔁 Skill Transfer",
    "🌎 Geographical Summary"
])

# 1. Summary Tab
with tab1:
    st.subheader("Professional Summary (AI)")
    if st.button("Generate Summary", key="summary"):
        with st.spinner("Generating professional summary..."):
            summary, prompt, fields_used = generate_nurse_summary_for_user(selected_user, filtered_df)
            st.success("✅ Summary Generated")
            st.code(summary)

            with st.expander("🧾 Prompt Sent to OpenAI"):
                st.code(prompt, language="markdown")

            with st.expander("📋 Fields Used"):
                for i, job in enumerate(fields_used, 1):
                    st.markdown(f"**Job #{i}:**")
                    st.json(job)

# 2. Culture Tab (placeholder)
with tab2:
    st.subheader("Culture Summary (Manual Input Playground)")

    with st.form("culture_input_form"):
        st.markdown("### 🧑‍⚕️ Enter Nurse's Ratings")

        col1, col2 = st.columns(2)
        with col1:
            unit_culture_rating = st.slider("Unit Culture", 1.0, 5.0, 3.0, step=0.1)
            benefits_rating = st.slider("Benefits", 1.0, 5.0, 3.0, step=0.1)
        with col2:
            growth_rating = st.slider("Growth Opportunities", 1.0, 5.0, 3.0, step=0.1)
            hospital_rating = st.slider("Hospital Quality", 1.0, 5.0, 3.0, step=0.1)

        general_feedback = st.text_area("General Feedback (optional)", placeholder="Describe team, management, culture, etc.")

        st.markdown("### 📊 Enter Cohort Averages (optional)")
        col3, col4 = st.columns(2)
        with col3:
            avg_unit = st.number_input("Avg Unit Culture", 1.0, 5.0, 3.5, step=0.1)
            avg_benefits = st.number_input("Avg Benefits", 1.0, 5.0, 3.5, step=0.1)
        with col4:
            avg_growth = st.number_input("Avg Growth Opportunities", 1.0, 5.0, 3.5, step=0.1)
            avg_hospital = st.number_input("Avg Hospital Quality", 1.0, 5.0, 3.5, step=0.1)

        submitted = st.form_submit_button("Generate Culture Summary")

    if submitted:
        user_inputs = {
            "unit_culture_rating": unit_culture_rating,
            "benefits_rating": benefits_rating,
            "growth_opportunities_rating": growth_rating,
            "hospital_quality_rating": hospital_rating,
            "general_feedback": general_feedback.strip(),
        }

        cohort_averages = {
            "unit_culture_rating": avg_unit,
            "benefits_rating": avg_benefits,
            "growth_opportunities_rating": avg_growth,
            "hospital_quality_rating": avg_hospital,
        }

        with st.spinner("Generating culture summary..."):
            summary, prompt, inputs_used = generate_culture_summary_from_inputs(user_inputs, cohort_averages)

            if not summary:
                st.warning("🚫 Not enough input to generate a culture summary.")
            else:
                st.success("✅ Culture Summary")
                st.markdown(summary)

                with st.expander("🧾 Prompt Sent to OpenAI"):
                    st.code(prompt, language="markdown")

                with st.expander("📋 Inputs Used"):
                    st.json(inputs_used)

# 3. Skill Transfer Tab
with tab3:
    st.subheader("Skill Transfer Insights")

    user_specialty = user_rows['specialty'].iloc[0]
    user_base_pay = user_rows['base_pay'].iloc[0]
    years_group = user_rows['total_years_of_experience_group'].iloc[0]
    state = user_rows['state'].iloc[0]

    if not user_specialty or pd.isna(user_specialty):
        st.warning("🚫 No specialty info available for the selected user.")
    elif pd.isna(user_base_pay):
        st.warning("⚠️ Base pay is missing — cannot compare to national averages.")
    else:
        st.markdown(f"**Current Specialty:** `{user_specialty}` at ${user_base_pay}/hr")

        if st.button("Show Potential Transfers", key="skills"):
            with st.spinner("Analyzing skill overlap and compensation..."):
                error_msg, suggestions_df = compute_skill_transfer_options(
                    specialty=user_specialty,
                    user_base_pay=user_base_pay,
                    years_of_experience_group=years_group,
                    state=state,
                    skills_df=skills_overlap_df,
                    avg_pay_df=average_pay_df
                )

                if error_msg:
                    st.warning(error_msg)
                else:
                    st.success("✅ Top Specialty Transitions Based on Skills & Pay")

                    raw_bullets = []
                    for _, row in suggestions_df.iterrows():
                        skills = row["shared_skill_names"]
                        skill_text = skills if isinstance(skills, str) else ", ".join(list(skills))
                        bullet = f"• {row['specialty_2']}: +${row['pay_increase']:.0f}/hr — uses skills like {skill_text.lower()}"
                        raw_bullets.append(bullet)

                    polished_bullets, prompt = refine_skill_transfer_bullets(
                        specialty=user_specialty,
                        raw_bullets=raw_bullets
                    )

                    for bullet in polished_bullets:
                        st.markdown(bullet)

                    # Optional: Show detailed computation breakdown
                    with st.expander("🔍 See How These Suggestions Were Calculated"):
                        st.markdown("These suggestions are based on:")

                        st.markdown(f"""
                        - **Your Specialty:** `{user_specialty}`
                        - **Your Base Pay:** `${user_base_pay}/hr`
                        - **Experience Group:** `{years_group}`
                        - **Location (State):** `{state}`
                        - **Data Sources:**
                            - Skill Overlap: `{skills_overlap_df.shape[0]}` records analyzed
                            - Compensation Benchmarks: Filtered by specialty, state, and experience group
                        """)

                        # Show a breakdown table
                        st.write(suggestions_df)

                    with st.expander("🧾 Prompt Sent to OpenAI for Bullet Refinement"):
                        st.code(prompt, language="markdown")


# 4. Geographical Summary Tab
with tab4:
    st.subheader("Summary")
    state_counts = nursing_df['state'].value_counts().reset_index()
    state_counts.columns = ['State', 'Count']
    st.bar_chart(state_counts.set_index('State'))

    # Summary table of specialties by total years of experience (use average pay data)
    st.subheader("Specialties by Experience Level")
    exp_specialty = average_pay_df.groupby(['total_years_of_experience_group', 'specialty']).agg(
        num_jobs=('specialty', 'count'),
        avg_base_pay=('avg_base_pay', 'mean')
    ).reset_index()
    st.dataframe(exp_specialty, use_container_width=True)
