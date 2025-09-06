import streamlit as st
import pandas as pd
from auth import check_password, logout
from config.settings import APP_CONFIG, AI_MODELS
from data.loaders import load_all_data
from services.insight_service import InsightService
from ui.components import UserSelector, ParameterControls, DataDisplay, SessionCostSummary
from ui.insights import ProfessionalSummaryView, CultureAnalysisView, SkillTransferView
from utils.cost_calculator import update_pricing

# App config
st.set_page_config(**APP_CONFIG)

# Password protection
if not check_password():
    st.stop()

# Main app header with logout and refresh options
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.title("🧠 Nurse AI Insights - Complete Transparency")
    st.caption("See all inputs, parameters, and prompts BEFORE generating")
with col2:
    if st.button("🔄 Refresh Data", help="Clear cache and reload all data"):
        # Clear all cached data
        st.cache_data.clear()
        st.success("Data refreshed!")
        st.rerun()
with col3:
    if st.button("🚪 Logout", help="Clear session and logout"):
        logout()

# Initialize services
@st.cache_data
def get_data():
    return load_all_data()

# Load data and create service instance
data = get_data()

# Create insight service (don't cache this as it contains OpenAI client)
try:
    insight_service = InsightService()
    st.sidebar.success("✅ InsightService initialized")
except Exception as e:
    st.sidebar.error(f"❌ Failed to initialize InsightService: {e}")
    st.stop()

# Cost tracking sidebar
with st.sidebar:
    st.header("💰 Cost Tracking")
    SessionCostSummary.render()
    st.divider()
    update_pricing()

# User selection
user_selector = UserSelector(data['nursing_df'], data['ai_insights_df'])
selected_user_id, user_data = user_selector.render()

if selected_user_id is None:
    st.stop()

st.divider()

# Main insight type selector
insight_type = st.radio(
    "Choose insight type to see complete breakdown:", 
    ["Professional Summary", "Culture Analysis", "Skill Transfer"],
    horizontal=True
)

st.divider()

# Render the appropriate insight view
if insight_type == "Professional Summary":
    view = ProfessionalSummaryView(insight_service, data, selected_user_id, user_data)
    view.render()
elif insight_type == "Culture Analysis":
    view = CultureAnalysisView(insight_service, data, selected_user_id, user_data)
    view.render()
else:  # Skill Transfer
    view = SkillTransferView(insight_service, data, selected_user_id, user_data)
    view.render()