import streamlit as st
import pandas as pd
from data.loaders import get_existing_insight
from config.settings import AI_MODELS, PARAMETER_DESCRIPTIONS

class UserSelector:
    """Component for selecting users with filtering"""
    
    def __init__(self, nursing_df, ai_insights_df):
        self.nursing_df = nursing_df
        self.ai_insights_df = ai_insights_df
    
    def render(self):
        """Render user selector and return selected user_id and data"""
        col1, col2 = st.columns(2)
        
        with col1:
            specialties = ["All"] + sorted(self.nursing_df['specialty'].dropna().unique().tolist())
            selected_specialty = st.selectbox("Filter by specialty", specialties)

        with col2:
            filtered_df = self.nursing_df.copy()
            if selected_specialty != "All":
                filtered_df = filtered_df[filtered_df['specialty'] == selected_specialty]
            
            # Sort users: real names first, then dummy users
            if 'sort_priority' in filtered_df.columns:
                picker_df = filtered_df.drop_duplicates(subset=["user_id"]).sort_values(['sort_priority', 'display_name'])
            else:
                picker_df = filtered_df.drop_duplicates(subset=["user_id"]).sort_values('display_name')
            
            user_options = picker_df['display_name'].tolist()
            if not user_options:
                st.error("No users match filters")
                return None, None
            
            selected_display = st.selectbox("Select user", user_options)
            selected_user_id = picker_df[picker_df['display_name'] == selected_display]['user_id'].iloc[0]
        
        user_data = self.nursing_df[self.nursing_df['user_id'] == selected_user_id].copy()
        return selected_user_id, user_data

class ParameterControls:
    """Component for AI parameter controls"""
    
    def __init__(self, insight_type):
        self.insight_type = insight_type
        self.config = AI_MODELS[insight_type.lower().replace(" ", "_")]
    
    def render(self):
        """Render parameter controls and return selected values"""
        st.subheader("⚙️ AI Parameters")
        
        param_col1, param_col2, param_col3 = st.columns(3)
        
        with param_col1:
            model = st.selectbox(
                "Model", 
                self.config["model_options"], 
                index=self.config["model_options"].index(self.config["default_model"]),
                help=PARAMETER_DESCRIPTIONS["model"]["help"]
            )
            st.caption(PARAMETER_DESCRIPTIONS["model"]["details"])
            
        with param_col2:
            temperature = st.slider(
                "Temperature", 
                0.0, 1.0, 
                self.config["default_temperature"], 
                0.1,
                help=PARAMETER_DESCRIPTIONS["temperature"]["help"]
            )
            st.caption(PARAMETER_DESCRIPTIONS["temperature"]["details"])
            
        with param_col3:
            max_tokens = st.slider(
                "Max Tokens", 
                50, 500, 
                self.config["default_max_tokens"], 
                10,
                help=PARAMETER_DESCRIPTIONS["max_tokens"]["help"]
            )
            st.caption(PARAMETER_DESCRIPTIONS["max_tokens"]["details"])
        
        return model, temperature, max_tokens

class DataDisplay:
    """Component for displaying user data"""
    
    @staticmethod
    def show_user_header(user_data, selected_user_id):
        """Show user header with name and basic info"""
        if not user_data.empty:
            first_row = user_data.iloc[0]
            user_name = f"{first_row.get('first_name', 'No First')} {first_row.get('last_name', 'No Last')}"
            st.subheader(f"👤 {user_name}")
            st.write(f"**User ID:** {selected_user_id} | **Email:** {first_row.get('email', 'N/A')}")
    
    @staticmethod
    def show_existing_insight_status(ai_insights_df, selected_user_id, insight_type):
        """Show existing insight status"""
        existing_insight = get_existing_insight(ai_insights_df, selected_user_id, insight_type)
        if existing_insight:
            st.success("✅ Existing insight found")
            with st.expander("View existing insight"):
                st.write(existing_insight)
        else:
            st.info("ℹ️ No existing insight - will generate new")
        return existing_insight
    
    @staticmethod
    def show_prompt_and_system(prompt, system_prompt):
        """Show the generated prompt and system prompt"""
        st.subheader("📝 Generated Prompt")
        st.code(prompt, language="text")
        st.write(f"**System Prompt:** `{system_prompt}`")