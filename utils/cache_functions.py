import streamlit as st
import pandas as pd
from sqlalchemy import text, create_engine

# Initialize database engine
@st.cache_resource
def get_database_engine():
    """Get database engine from Streamlit secrets"""
    return create_engine(st.secrets["database"]["DATABASE_URL"])

@st.cache_data(ttl=600)
def load_nursing_data():
    """
    Load nursing data with user profiles, job details, and culture ratings.
    
    Returns:
        pd.DataFrame: Combined nursing data with user and job information
    """
    engine = get_database_engine()
    
    sql = text("""
    WITH ranked_jobs AS (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY employment_start_date DESC NULLS LAST) as rn
        FROM jobs
    ),
    filtered_jobs AS (
        SELECT * FROM ranked_jobs WHERE rn = 1
    )
    SELECT 
        u.id as user_id,
        pi.nursing_degree,
        pi.total_years_of_experience_group,
        pi.total_years_of_experience,
        j.hospital,
        j.organization_city as city,
        j.organization_state as state,
        nursing_role,
        s.name as specialty,
        jd.sub_specialty,
        jd.shift_type,
        jd.employment_type,
        jd.base_pay,
        jd.base_pay_unit,
        jd.nurse_to_patient_ratio,
        jd.certifications,
        jd.unionized,
        d.total_differential,
        d.differentials,
        d.differentials_free_text,
        c.unit_culture_rating,
        c.benefits_rating,
        c.growth_opportunities_rating,
        c.hospital_quality_rating,
        c.general_feedback
    FROM users u
    LEFT JOIN professional_info pi ON u.id = pi.user_id
    LEFT JOIN filtered_jobs j ON u.id = j.user_id
    LEFT JOIN job_details jd ON j.id = jd.job_id
    LEFT JOIN specialties s ON jd.specialty_id = s.id
    LEFT JOIN differentials_summary d ON j.id = d.job_id
    LEFT JOIN culture c ON j.id = c.job_id
    """)

    nursing_df = pd.read_sql(sql, engine)

    # Clean data by removing rows with too many missing values
    threshold = 0.1 * nursing_df.shape[1]  # Keep rows with at least 10% of columns filled
    nursing_df_cleaned = nursing_df.dropna(thresh=threshold)

    return nursing_df_cleaned

@st.cache_data(ttl=600)
def skills_overlap():
    """
    Load specialty skill overlap data showing which skills are shared between specialties.
    
    Returns:
        pd.DataFrame: Skill overlap data with specialty names and shared skills
    """
    engine = get_database_engine()
    
    sql = text("""
    SELECT
        s1.name as specialty_1,
        o.specialty_1_id,
        s2.name as specialty_2,
        o.specialty_2_id,
        o.shared_skills,
        o.total_skills,
        o.overlap_percentage,
        o.shared_skill_names,
        o.avg_importance
    FROM public.specialty_skill_overlap o
    LEFT JOIN specialties s1 ON o.specialty_1_id = s1.id
    LEFT JOIN specialties s2 ON o.specialty_2_id = s2.id
    """)
    
    return pd.read_sql(sql, engine)

@st.cache_data(ttl=600)
def specialty_compensation():
    """
    Load specialty compensation statistics showing pay ranges by specialty.
    
    Returns:
        pd.DataFrame: Compensation statistics by specialty
    """
    engine = get_database_engine()
    
    sql = text("""
    SELECT
        specialty_id,
        specialties.name as specialty,
        COUNT(*) as num_jobs,
        AVG(base_pay) as avg_base_pay,
        MIN(base_pay) as min_base_pay,
        MAX(base_pay) as max_base_pay,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY base_pay) as p25_base_pay,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY base_pay) as median_base_pay,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY base_pay) as p75_base_pay
    FROM job_details
    LEFT JOIN specialties ON job_details.specialty_id = specialties.id
    WHERE base_pay IS NOT NULL
    GROUP BY specialty_id, specialties.name
    """)
    
    return pd.read_sql(sql, engine)

@st.cache_data(ttl=600)
def average_pay_model():
    """
    Load average pay data segmented by experience group, specialty, and state.
    
    Returns:
        pd.DataFrame: Average pay model data for skill transfer analysis
    """
    engine = get_database_engine()
    
    sql = text("""
    SELECT
        total_years_of_experience_group,
        s.name as specialty,
        organization_state as state,
        COUNT(*) as num_jobs,
        AVG(base_pay) as avg_base_pay,
        MIN(base_pay) as min_base_pay,
        MAX(base_pay) as max_base_pay,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY base_pay) as p25_base_pay,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY base_pay) as median_base_pay,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY base_pay) as p75_base_pay
    FROM job_details jd
    LEFT JOIN specialties s ON jd.specialty_id = s.id
    LEFT JOIN jobs j ON jd.job_id = j.id
    LEFT JOIN professional_info pi ON j.user_id = pi.user_id
    WHERE total_years_of_experience_group IS NOT NULL
    GROUP BY total_years_of_experience_group, s.name, organization_state
    """)
    
    return pd.read_sql(sql, engine)

@st.cache_data(ttl=600)
def load_ai_insights():
    """
    Load existing AI insights to avoid regenerating content.
    
    Returns:
        pd.DataFrame: AI insights with user information
    """
    engine = get_database_engine()
    
    sql = text("""
    SELECT 
        user_id, 
        summary_type, 
        content, 
        first_name, 
        last_name, 
        email, 
        u.completed_onboarding, 
        ai.created_at 
    FROM public.ai_insights ai 
    LEFT JOIN public.users u ON u.id = ai.user_id 
    """)
    
    return pd.read_sql(sql, engine)

# Helper function for data quality checks
def check_data_quality(df, table_name):
    """
    Check data quality and log basic statistics.
    
    Args:
        df (pd.DataFrame): DataFrame to check
        table_name (str): Name of the table for logging
    
    Returns:
        dict: Basic quality metrics
    """
    if df.empty:
        st.warning(f"⚠️ {table_name} is empty")
        return {"status": "empty", "rows": 0, "columns": 0}
    
    metrics = {
        "status": "loaded",
        "rows": len(df),
        "columns": len(df.columns),
        "missing_percentage": (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
    }
    
    return metrics