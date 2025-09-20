import streamlit as st
import pandas as pd
from openai import OpenAI
from config.settings import AI_MODELS

class InsightService:
    """Service for generating AI insights for nurses"""
    
    def __init__(self):
        self.client = OpenAI(api_key=st.secrets["OPENAI_KEY"])
    
    def build_professional_summary_prompt(self, user_data):
        """Build the prompt for professional summary without calling the API"""
        if user_data.empty:
            return "No data available", []

        first = user_data.iloc[0]
        degree = first.get('nursing_degree', 'Unknown')
        experience = first.get('total_years_of_experience', 'Unknown')
        
        # Build job summaries
        job_summaries = []
        for _, row in user_data.iterrows():
            role = row.get('nursing_role', 'Nurse')
            specialty = row.get('specialty', 'General Practice')
            hospital = row.get('hospital', 'healthcare facility')
            city = row.get('city', '')
            state = row.get('state', '')
            location = f"{city}, {state}".strip(', ') or "unspecified location"
            pay = row.get('base_pay')
            
            summary = f"{role} specializing in {specialty} at {hospital} in {location}"
            if pay:
                summary += f", earning ${pay}/hr"
            
            job_summaries.append(summary)

        job_text = "\n".join(f"- {s}" for s in job_summaries)

        prompt = f"""This nurse holds a degree in {degree} and has {experience} years of experience.

They've worked in the following roles:
{job_text}

Write a professional 1-2 sentence summary of this nurse. Highlight their experience, strengths, and growth. The tone should be positive and empowering. Avoid bullet points or robotic repetition — synthesize the information into a fluid narrative under 40 words."""

        return prompt, []
    
    def generate_professional_summary(self, user_data, model, temperature, max_tokens, custom_system_prompt=None, custom_general_prompt=None):
        """Generate professional summary for a nurse"""
        # Use custom prompt if provided and not empty, otherwise use default
        if custom_general_prompt and custom_general_prompt.strip():
            prompt = custom_general_prompt.strip()
        else:
            prompt, _ = self.build_professional_summary_prompt(user_data)

        if prompt == "No data available":
            return "No data found", "N/A", []

        system_prompt = custom_system_prompt or AI_MODELS["professional_summary"]["system_prompt"]

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content.strip(), prompt, []
        except Exception as e:
            return f"Error: {e}", prompt, []
    
    def build_culture_analysis_prompt(self, user_ratings, cohort_averages):
        """Build the prompt for culture analysis without calling the API"""
        if all(v in [None, "", "NaN"] or pd.isna(v) for v in user_ratings.values()):
            return None, {}

        prompt = f"""You're generating culture insights based on ratings and open feedback. Keep the tone clear, direct, and approachable.

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

Return only 3 concise bullet points. No intro. No wrap-up."""

        return prompt, user_ratings
    
    def generate_culture_analysis(self, user_ratings, cohort_averages, model, temperature, max_tokens, custom_system_prompt=None, custom_general_prompt=None):
        """Generate culture analysis from ratings"""
        # Use custom prompt if provided and not empty, otherwise use default
        if custom_general_prompt and custom_general_prompt.strip():
            prompt = custom_general_prompt.strip()
        else:
            prompt, validated_ratings = self.build_culture_analysis_prompt(user_ratings, cohort_averages)

        if prompt is None:
            return None, None, {}

        system_prompt = custom_system_prompt or AI_MODELS["culture_analysis"]["system_prompt"]

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content.strip(), prompt, user_ratings
        except Exception as e:
            return f"Error: {e}", prompt, user_ratings
    
    def build_skill_transfer_prompt(self, specialty, raw_bullets):
        """Build the prompt for skill transfer without calling the API"""
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
- Use soft, suggestive language like "may offer", "could align with", "might be a fit"
- Avoid personal pronouns like "you"
- Each bullet must fit on one line
- Keep the +$X/hr formatting
- Do not overpromise or sound directive

Output only the bullet points."""

        return prompt
    
    def generate_skill_transfer_suggestions(self, specialty, raw_bullets, model, temperature, max_tokens, custom_system_prompt=None, custom_general_prompt=None):
        """Generate refined skill transfer suggestions"""
        # Use custom prompt if provided and not empty, otherwise use default
        if custom_general_prompt and custom_general_prompt.strip():
            prompt = custom_general_prompt.strip()
        else:
            prompt = self.build_skill_transfer_prompt(specialty, raw_bullets)

        system_prompt = custom_system_prompt or AI_MODELS["skill_transfer"]["system_prompt"]

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content.strip()
            lines = content.split("\n")
            cleaned = [line.strip() for line in lines if line.strip()]
            return cleaned, prompt
        except Exception as e:
            return [f"Error: {e}"], prompt
    
    def compute_skill_transfer_options(self, specialty, user_base_pay, years_of_experience_group, state, skills_df, avg_pay_df):
        """Compute skill transfer options based on specialty overlap and pay data"""
        if not specialty or pd.isna(specialty):
            return "'specialty' is missing or null", pd.DataFrame()

        overlaps = skills_df[
            skills_df["specialty_1"].str.lower() == specialty.lower()
        ]
        if overlaps.empty:
            return "No skill overlap data available.", pd.DataFrame()

        avg_df = avg_pay_df[
            (avg_pay_df["total_years_of_experience_group"] == years_of_experience_group)
            & (avg_pay_df["state"] == state)
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

        def safe_parse_skills(x):
            """Safely parse skill names from string representation"""
            if not isinstance(x, str):
                return []
            
            # Remove brackets and quotes, split by comma
            cleaned = x.strip('[]').replace("'", "").replace('"', '')
            if not cleaned:
                return []
            
            skills = [skill.strip() for skill in cleaned.split(',')]
            return [skill for skill in skills if skill]  # Remove empty strings
        
        merged["shared_skill_names"] = merged["shared_skill_names"].apply(safe_parse_skills)

        top_matches = merged.sort_values("pay_increase", ascending=False).head(5).copy()

        top_matches = top_matches[[
            "specialty_2", "avg_base_pay", "pay_increase",
            "shared_skill_names", "avg_importance", "overlap_percentage",
            "total_years_of_experience_group", "state"
        ]]

        return None, top_matches