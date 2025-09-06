import streamlit as st
import pandas as pd
from utils.cache_functions import (
    load_nursing_data,
    skills_overlap,
    specialty_compensation,
    average_pay_model,
    load_ai_insights,
)

@st.cache_data(ttl=600)
def load_all_data():
    """Load all required data for the application"""
    nursing_df = load_nursing_data()
    skills_df = skills_overlap()
    specialty_comp_df = specialty_compensation()
    avg_pay_df = average_pay_model()
    ai_insights_df = load_ai_insights()
    
    # Fix names issue - merge from ai_insights if needed
    if 'first_name' not in nursing_df.columns and not ai_insights_df.empty:
        name_data = ai_insights_df[['user_id', 'first_name', 'last_name', 'email']].drop_duplicates('user_id')
        nursing_df = nursing_df.merge(name_data, on='user_id', how='left')
    
    # Create display names with simple sorting priority
    if all(col in nursing_df.columns for col in ['first_name', 'last_name']):
        nursing_df['display_name'] = nursing_df.apply(
            lambda r: f"{r.get('first_name', 'No First')} {r.get('last_name', 'No Last')} - {r.get('specialty', 'No Specialty')}", 
            axis=1
        )
        # Create sort order: only put None/null users last, keep everything else at top
        def get_sort_priority(row):
            first_name = str(row.get('first_name', '')).strip().lower()
            last_name = str(row.get('last_name', '')).strip().lower()
            
            # Only filter out None/null/empty values - keep test data visible
            invalid_names = ['', 'none', 'no first', 'no last', 'nan', 'null']
            
            # Check if names are invalid/empty
            first_is_invalid = first_name in invalid_names
            last_is_invalid = last_name in invalid_names
            
            # Real user if both names exist (including test accounts)
            if not first_is_invalid and not last_is_invalid:
                return 0  # Real users AND test users first
            else:
                return 1  # Only None/null users last
        
        nursing_df['sort_priority'] = nursing_df.apply(get_sort_priority, axis=1)
    else:
        nursing_df['display_name'] = nursing_df.apply(
            lambda r: f"User {r['user_id']} - {r.get('specialty', 'No Specialty')}", axis=1
        )
        nursing_df['sort_priority'] = 1  # All get same priority if no names
    
    return {
        'nursing_df': nursing_df,
        'skills_df': skills_df,
        'specialty_comp_df': specialty_comp_df,
        'avg_pay_df': avg_pay_df,
        'ai_insights_df': ai_insights_df
    }

def get_existing_insight(ai_insights_df, user_id, insight_type):
    """Get existing AI insight for a user and insight type"""
    from config.settings import INSIGHT_TYPE_MAPPING
    
    if ai_insights_df.empty:
        return None
    
    db_type = INSIGHT_TYPE_MAPPING.get(insight_type)
    if not db_type:
        return None

    # Check user_id matches
    user_matches = ai_insights_df[ai_insights_df['user_id'] == user_id]
    
    # Check summary_type matches
    type_matches = ai_insights_df[ai_insights_df['summary_type'] == db_type]
    
    user_insights = ai_insights_df[
        (ai_insights_df['user_id'] == user_id) & 
        (ai_insights_df['summary_type'] == db_type)
    ]
    
    if user_insights.empty:
        return None
    
    latest = user_insights.sort_values('created_at', ascending=False).iloc[0]
    return latest['content']