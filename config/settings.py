# Configuration settings for the Nurse AI Insights app

APP_CONFIG = {
    "page_title": "Nurse AI Insights - Simple",
    "layout": "wide"
}

AI_MODELS = {
    "professional_summary": {
        "default_model": "gpt-4o",
        "default_temperature": 0.7,
        "default_max_tokens": 150,
        "model_options": ["gpt-4o-mini", "gpt-4o", "gpt-4"],
        "system_prompt": (
            "You are a career summary assistant for nursing professionals. "
            "Your job is to generate a personalized, motivational summary based on job history. "
            "Keep it under 40 words. Do not repeat exact job facts. Focus on impact, specialization, and value."
        )
    },
    "culture_analysis": {
        "default_model": "gpt-4o-mini",
        "default_temperature": 0.5,
        "default_max_tokens": 200,
        "model_options": ["gpt-4o-mini", "gpt-4o", "gpt-4"],
        "system_prompt": (
            "You write short, professional workplace insights from survey ratings. "
            "Output only clear, readable bullet points. "
            "No fluff. No AI-sounding sentences. No references to 'user' or 'nurse'. Focus on what matters."
        )
    },
    "skill_transfer": {
        "default_model": "gpt-4o",
        "default_temperature": 0.3,
        "default_max_tokens": 250,
        "model_options": ["gpt-4o-mini", "gpt-4o", "gpt-4"],
        "system_prompt": (
            "Rewrite raw nursing specialty suggestions into short, professional bullet points. "
            "Each bullet should describe a possible career transition, highlight a potential pay increase, "
            "and reference relevant skills in plain English. "
            "Avoid personal pronouns and definitive promises. Use cautious, suggestive language."
        )
    }
}

PARAMETER_DESCRIPTIONS = {
    "temperature": {
        "help": "Controls randomness and creativity in responses",
        "details": "0.0 = Very focused and deterministic | 1.0 = More creative and varied"
    },
    "max_tokens": {
        "help": "Maximum length of the AI response", 
        "details": "Higher values allow longer responses but may include unnecessary content"
    },
    "model": {
        "help": "Different AI models with varying capabilities",
        "details": "gpt-4o = Most capable | gpt-4o-mini = Faster and cost-effective | gpt-4 = Previous generation"
    }
}

# Database table mappings for insights
INSIGHT_TYPE_MAPPING = {
    "Professional Summary": "nurse_summary",  # Changed from "professional_summary"
    "Culture Analysis": "culture",              # Changed from "culture_summary" 
    "Skill Transfer": "skill_transfer"         # This one matches
}