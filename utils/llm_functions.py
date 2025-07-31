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

    prompt = f"""
You're generating culture insights based on ratings and open feedback. Keep the tone clear, direct, and approachable.

Output a list of 3 bullet points — each under 15 words.

Avoid clinical terms and words like "user" or "the nurse."
Never use phrases like "might suggest" or "could be" — just state the facts.
Only compare to cohort averages when the difference is meaningful (> 0.2).
Skip general statements that add no new info.
If general feedback is useful, include it in a bullet.
Use light emoji accents where it helps readability (e.g. 📈, 💬, 👥, 👍, 👎).

Ratings:
- Unit Culture: {user_ratings['unit_culture_rating']}
- Benefits: {user_ratings['benefits_rating']}
- Growth Opportunities: {user_ratings['growth_opportunities_rating']}
- Hospital Quality: {user_ratings['hospital_quality_rating']}

Feedback: "{user_ratings['general_feedback']}"

Cohort Averages:
- Unit Culture: {cohort_averages.get('unit_culture_rating')}
- Benefits: {cohort_averages.get('benefits_rating')}
- Growth Opportunities: {cohort_averages.get('growth_opportunities_rating')}
- Hospital Quality: {cohort_averages.get('hospital_quality_rating')}

Return only 3 concise bullet points. No intro. No wrap-up.
"""

    system_prompt = (
    "You write short, professional workplace insights from survey ratings. Output only clear, readable bullet points. "
    "No fluff. No AI-sounding sentences. No references to 'user' or 'nurse'. Focus on what matters."
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

def compute_skill_transfer_options(specialty, user_base_pay, years_of_experience_group, state, skills_df, avg_pay_df):
    overlaps = skills_df[skills_df["specialty_1"].str.lower() == specialty.lower()]
    if overlaps.empty:
        return "No skill overlap data available.", pd.DataFrame()

    avg_df = avg_pay_df[
        (avg_pay_df["total_years_of_experience_group"] == years_of_experience_group) &
        (avg_pay_df["state"] == state)
    ]

    merged = overlaps.merge(
        avg_df,
        left_on="specialty_2",
        right_on="specialty",
        how="left"
    ).dropna(subset=["avg_base_pay"])

    merged["pay_increase"] = merged["avg_base_pay"] - user_base_pay
    merged = merged[merged["pay_increase"] > 0]

    if merged.empty:
        return "No higher-paying specialties with strong skill overlap found.", pd.DataFrame()

    merged["shared_skill_names"] = merged["shared_skill_names"].apply(
        lambda x: eval(x) if isinstance(x, str) else []
    )
    merged["top_skills"] = merged["shared_skill_names"].apply(
        lambda x: ", ".join(list(x)[:2]) if isinstance(x, (list, set)) else ""
    )

    top_matches = merged.sort_values("pay_increase", ascending=False).head(5).copy()

    # Select key fields for display
    top_matches = top_matches[[
        "specialty_2", "avg_base_pay", "pay_increase",
        "shared_skill_names", "avg_importance", "overlap_percentage",
        "total_years_of_experience_group", "state"
    ]]

    top_matches["top_skills"] = top_matches["shared_skill_names"].apply(
        lambda x: ", ".join(x[:2]) if isinstance(x, list) and len(x) >= 2 else ", ".join(x)
    )

    return None, top_matches

def refine_skill_transfer_bullets(specialty: str, raw_bullets: list[str]) -> list[str]:
    bullet_block = "\n".join(raw_bullets)

    prompt = f"""A nurse currently works in the {specialty} specialty.

Below are raw suggestions for potential specialty transitions with higher pay:
{bullet_block}

Rewrite these as 2-4 short, professional bullet points.

Each bullet should:
- Mention the suggested specialty
- Indicate an approximate potential pay increase (e.g., +$X/hr)
- Briefly mention relevant skill areas (in layman's terms), but acknowledge these are based on general specialty overlaps

Guidelines:
- Be cautious — do not assume the nurse has these skills
- Use soft, suggestive language like “may offer”, “could align with”, “might be a fit”
- Avoid personal pronouns like "you"
- Each bullet must fit on one line
- Keep the +$X/hr formatting
- Do not overpromise or sound directive

Output only the bullet points.
"""

    system_prompt = (
        "Rewrite raw nursing specialty suggestions into short, professional bullet points. "
        "Each bullet should describe a possible career transition, highlight a potential pay increase, and reference relevant skills in plain English. "
        "Avoid personal pronouns, soft recommendations, or definitive promises."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        result = response.choices[0].message.content.strip()
        return [line.strip() for line in result.split("\n") if line.strip()], prompt
    except Exception as e:
        return [f"⚠️ GPT Error: {e}"]

