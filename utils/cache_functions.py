import streamlit as st
import pandas as pd
from sqlalchemy import text, create_engine

engine = create_engine(st.secrets["database"]["DATABASE_URL"])

@st.cache_data(ttl=600)
def load_nursing_data():
    sql = text("""
with ranked_jobs as (
  select *,
         row_number() over (partition by user_id order by employment_start_date desc nulls last) as rn
  from jobs
),
filtered_jobs as (
  select * from ranked_jobs where rn = 1
)
select 
  u.id as user_id,
  pi.nursing_degree,
  pi.total_years_of_experience_group,
  pi.total_years_of_experience,
  j.hospital,
  j.organization_city as city,
  j.organization_state as state,
  nursing_role,
  jd.specialty,
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
from users u
left join professional_info pi on u.id = pi.user_id
left join filtered_jobs j on u.id = j.user_id
left join job_details jd on j.id = jd.job_id
left join differentials_summary d on j.id = d.job_id
left join culture c on j.id = c.job_id""")

    nursing_df = pd.read_sql(sql, engine)

    # To work with the most complete data, we can drop rows with relatively high NaN counts
    threshold = 0.1 * nursing_df.shape[1]  # 55% of columns
    nursing_df_cleaned = nursing_df.dropna(thresh=threshold)

    return nursing_df_cleaned

@st.cache_data(ttl=600)
def skills_overlap():
    skills_df = pd.read_sql(text("""
    select
        s1.name as specialty_1,
        o.specialty_1_id,
        s2.name as specialty_2,
        o.specialty_2_id,
        o.shared_skills,
        o.total_skills,
        o.overlap_percentage
    from public.specialty_skill_overlap o
    left join specialties s1
        on o.specialty_1_id = s1.id
    left join specialties s2
        on o.specialty_2_id = s2.id
    """), engine)
    return skills_df

@st.cache_data(ttl=600)
def specialty_compensation():
    comp_df = pd.read_sql(text("""
    select
        specialty_id,
        specialty,
        count(*) as num_jobs,
        avg(base_pay) as avg_base_pay,
        min(base_pay) as min_base_pay,
        max(base_pay) as max_base_pay,
        percentile_cont(0.25) within group (order by base_pay) as p25_base_pay,
        percentile_cont(0.5) within group (order by base_pay) as median_base_pay,
        percentile_cont(0.75) within group (order by base_pay) as p75_base_pay
    from job_details
    where base_pay is not null
    group by 1,2
    """), engine)
    return comp_df