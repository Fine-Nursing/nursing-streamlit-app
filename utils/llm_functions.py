from openai import OpenAI
import streamlit as st
import pandas as pd

client = OpenAI(api_key=st.secrets["OPENAI_KEY"])

def generate_nurse_summary_for_user(user_id, df):
    user_rows = df[df['user_id'] == user_id]
    if user_rows.empty:
        return "No data found", "N/A", []

    first = user_rows.iloc[0]
    used_fields = {
        "nursing_degree": first.get("nursing_degree"),
        "total_years_of_experience": first.get("total_years_of_experience"),
    }

    job_summaries = []
    job_details_list = []

    for _, row in user_rows.iterrows():
        detail_fields = {
            "nursing_role": row.get('nursing_role'),
            "specialty": row.get('specialty'),
            "hospital": row.get('hospital'),
            "city": row.get('city'),
            "state": row.get('state'),
            "base_pay": row.get('base_pay'),
            "shift_type": row.get('shift_type'),
            "employment_type": row.get('employment_type'),
            "unionized": row.get('unionized'),
            "differentials": row.get('differentials'),
            "unit_feedback": row.get('unit_feedback'),
        }
        job_details_list.append(detail_fields)

        role = detail_fields["nursing_role"] or "Nurse"
        specialty = detail_fields["specialty"] or "General Practice"
        hospital = detail_fields["hospital"] or "a healthcare facility"
        location = f"{detail_fields['city']}, {detail_fields['state']}" if detail_fields["city"] and detail_fields["state"] else "an unspecified location"

        summary = f"{role} specializing in {specialty} at {hospital} in {location}"
        if detail_fields["base_pay"]:
            summary += f", earning ${detail_fields['base_pay']}/hr"
        if detail_fields["differentials"]:
            summary += f" with additional differentials"
        if detail_fields["shift_type"]:
            summary += f", working {detail_fields['shift_type'].lower()} shifts"
        if detail_fields["employment_type"]:
            summary += f" as a {detail_fields['employment_type'].lower()} nurse"
        if detail_fields["unionized"] and str(detail_fields["unionized"]).lower() in ["yes", "true", "unionized"]:
            summary += ", part of a unionized team"
        if detail_fields["unit_feedback"]:
            summary += f". Peer feedback: \"{detail_fields['unit_feedback'].strip()}\""

        job_summaries.append(summary)

    job_text = "\n".join(f"- {s}" for s in job_summaries)
    prompt = f"""
This nurse holds a degree in {used_fields['nursing_degree']} and has {used_fields['total_years_of_experience']} years of experience.

They've worked in the following roles:
{job_text}

Write a professional 1-2 sentence summary of this nurse. Highlight their experience, strengths, and growth. The tone should be positive and empowering. Avoid bullet points or robotic repetition — synthesize the information into a fluid narrative under 40 words.
""".strip()

    system_prompt = (
        "You are a career summary assistant for nursing professionals. Your job is to generate a personalized, motivational summary based on job history. "
        "Keep it under 40 words. Do not repeat exact job facts. Focus on impact, specialization, and value."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content.strip(), prompt, job_details_list
    except Exception as e:
        return f"❌ OpenAI error for user_id {user_id}: {e}", prompt, job_details_list


def generate_culture_summary_from_inputs(user_ratings: dict, cohort_averages: dict):
    if all(v in [None, "", "NaN"] or pd.isna(v) for v in user_ratings.values()):
        return None, None, {}

    prompt = f"""You are analyzing a nurse's workplace experience based on the following inputs.

User Ratings:
- Unit Culture: {user_ratings['unit_culture_rating']}
- Benefits: {user_ratings['benefits_rating']}
- Growth Opportunities: {user_ratings['growth_opportunities_rating']}
- Hospital Quality: {user_ratings['hospital_quality_rating']}
- General Feedback: "{user_ratings['general_feedback']}"

Cohort Averages:
- Unit Culture: {cohort_averages.get('unit_culture_rating')}
- Benefits: {cohort_averages.get('benefits_rating')}
- Growth Opportunities: {cohort_averages.get('growth_opportunities_rating')}
- Hospital Quality: {cohort_averages.get('hospital_quality_rating')}

Write 3–4 bullet points summarizing this nurse's workplace experience. Include thoughtful comparison to the cohort average if relevant. Be empathetic, clear, and use emojis.
"""

    system_prompt = (
        "You are a professional assistant summarizing workplace culture insights based on survey ratings and written feedback. "
        "Create clear, concise, and positive bullet points that reflect real sentiment."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip(), prompt, user_ratings
    except Exception as e:
        return f"❌ OpenAI error: {e}", prompt, user_ratings

def compute_skill_transfer_options(specialty, user_base_pay, skills_df, comp_df):
    overlaps = skills_df[skills_df["specialty_1"].str.lower() == specialty.lower()]
    if overlaps.empty:
        return "No skill overlap data available.", []

    merged = overlaps.merge(
        comp_df,
        left_on="specialty_2_id",
        right_on="specialty_id",
        how="left"
    ).dropna(subset=["avg_base_pay"])

    merged["pay_increase"] = merged["avg_base_pay"] - user_base_pay
    merged = merged[merged["pay_increase"] > 0]

    if merged.empty:
        return "No higher-paying specialties with strong skill overlap found.", []

    top_matches = merged.sort_values("overlap_percentage", ascending=False).head(5)

    bullet_points = [
        f"• {row['specialty_2']}: +${row['pay_increase']:.0f}/hr vs current pay"
        for _, row in top_matches.iterrows()
    ]

    return None, bullet_points

def refine_skill_transfer_bullets(specialty: str, raw_bullets: list[str]) -> list[str]:
    bullet_block = "\n".join(raw_bullets)

    prompt = f"""A nurse currently works in the {specialty} specialty.

Here are raw specialty suggestions that offer higher pay:
{bullet_block}

Rewrite them as 2–4 direct, professional bullet points. Keep the +$X/hr part. Make each bullet one line only. Avoid vague terms like 'potential', 'growth', or 'flexibility'. Use sharp, clear, descriptive phrases. Do not say 'you'. Do not include soft recommendations.
Only return the bullet points.
"""

    system_prompt = (
        "You rewrite raw nursing specialty suggestions into direct, readable bullet points. Retain pay bump numbers (+$X/hr), and write clear 1-line descriptions. "
        "Avoid vague or fluffy wording. No personal language. No multi-line bullets."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=150
        )
        result = response.choices[0].message.content.strip()
        refined_bullets = [line.strip() for line in result.split("\n") if line.strip().startswith("•")]
        return refined_bullets
    except Exception as e:
        return [f"⚠️ GPT Error: {e}"]
