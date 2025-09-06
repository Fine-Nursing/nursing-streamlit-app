import streamlit as st
import pandas as pd
from ui.components import ParameterControls, DataDisplay
from config.settings import AI_MODELS

class ProfessionalSummaryView:
    """View component for Professional Summary insight"""
    
    def __init__(self, insight_service, data, selected_user_id, user_data):
        self.insight_service = insight_service
        self.data = data
        self.selected_user_id = selected_user_id
        self.user_data = user_data
    
    def render(self):
        # Show user info
        DataDisplay.show_user_header(self.user_data, self.selected_user_id)
        
        # Parameters
        param_controls = ParameterControls("Professional Summary")
        model, temperature, max_tokens = param_controls.render()
        
        # Input data breakdown
        st.subheader("📊 Input Data Being Used")
        
        if self.user_data.empty:
            st.warning("No data for this user")
            return
        
        first_row = self.user_data.iloc[0]
        
        # Profile data
        profile_col1, profile_col2 = st.columns(2)
        with profile_col1:
            st.write("**Profile Data:**")
            degree = first_row.get('nursing_degree', 'N/A')
            experience = first_row.get('total_years_of_experience', 'N/A')
            st.write(f"• Nursing Degree: `{degree}`")
            st.write(f"• Years Experience: `{experience}`")
        
        with profile_col2:
            st.write("**Job Count:**")
            st.write(f"• Total Jobs: `{len(self.user_data)}`")
        
        # Job details
        st.write("**Job History Details:**")
        for i, (_, job) in enumerate(self.user_data.iterrows(), 1):
            job_col1, job_col2, job_col3 = st.columns(3)
            
            with job_col1:
                st.write(f"**Job #{i}:**")
                st.write(f"• Role: `{job.get('nursing_role', 'N/A')}`")
                st.write(f"• Specialty: `{job.get('specialty', 'N/A')}`")
                st.write(f"• Hospital: `{job.get('hospital', 'N/A')}`")
                
            with job_col2:
                st.write(f"**Location & Pay:**")
                location = f"{job.get('city', '')}, {job.get('state', '')}".strip(', ') or 'N/A'
                st.write(f"• Location: `{location}`")
                st.write(f"• Base Pay: `${job.get('base_pay', 'N/A')}/hr`")
                st.write(f"• Shift: `{job.get('shift_type', 'N/A')}`")
                
            with job_col3:
                st.write(f"**Employment Details:**")
                st.write(f"• Type: `{job.get('employment_type', 'N/A')}`")
                st.write(f"• Unionized: `{job.get('unionized', 'N/A')}`")
                st.write(f"• Differentials: `{job.get('differentials', 'N/A')}`")
        
        # Build and show prompt
        system_prompt = AI_MODELS["professional_summary"]["system_prompt"]
        prompt, _ = self.insight_service.build_professional_summary_prompt(self.user_data)
        DataDisplay.show_prompt_and_system(prompt, system_prompt)
        
        # Check existing insight
        DataDisplay.show_existing_insight_status(
            self.data['ai_insights_df'], self.selected_user_id, "Professional Summary"
        )
        
        # Generate button
        if st.button("🚀 Generate Professional Summary", type="primary", use_container_width=True):
            try:
                with st.spinner("Generating..."):
                    content, prompt_used, job_details = self.insight_service.generate_professional_summary(
                        self.user_data, model, temperature, max_tokens
                    )
                    
                    if content and not content.startswith("Error:"):
                        st.subheader("✨ Generated Result:")
                        st.success(content)
                        st.caption("💡 Generation successful")
                    else:
                        st.error(content or "Generation failed")
                        
            except Exception as e:
                st.error(f"Error during generation: {str(e)}")

class CultureAnalysisView:
    """View component for Culture Analysis insight"""
    
    def __init__(self, insight_service, data, selected_user_id, user_data):
        self.insight_service = insight_service
        self.data = data
        self.selected_user_id = selected_user_id
        self.user_data = user_data
    
    def render(self):
        # Show user info
        DataDisplay.show_user_header(self.user_data, self.selected_user_id)
        
        # Parameters
        param_controls = ParameterControls("Culture Analysis")
        model, temperature, max_tokens = param_controls.render()
        
        # Input data section
        st.subheader("📊 Input Data Required")
        
        input_col1, input_col2 = st.columns(2)
        with input_col1:
            st.write("**Culture Ratings (1-5 scale):**")
            unit_culture = st.slider("Unit Culture", 1.0, 5.0, 3.0, 0.1)
            benefits = st.slider("Benefits", 1.0, 5.0, 3.0, 0.1)
            
        with input_col2:
            st.write("**Quality Ratings (1-5 scale):**")
            growth = st.slider("Growth Opportunities", 1.0, 5.0, 3.0, 0.1)
            hospital_quality = st.slider("Hospital Quality", 1.0, 5.0, 3.0, 0.1)
        
        general_feedback = st.text_area("General Feedback", placeholder="Optional feedback about workplace culture")
        
        # Show what's available in database
        if not self.user_data.empty:
            first_row = self.user_data.iloc[0]
            st.subheader("📋 Available in Database (for reference)")
            db_col1, db_col2 = st.columns(2)
            
            with db_col1:
                for col in ['unit_culture_rating', 'benefits_rating']:
                    val = first_row.get(col, 'N/A')
                    st.write(f"• {col.replace('_', ' ').title()}: `{val}`")
                    
            with db_col2:
                for col in ['growth_opportunities_rating', 'hospital_quality_rating']:
                    val = first_row.get(col, 'N/A')
                    st.write(f"• {col.replace('_', ' ').title()}: `{val}`")
            
            feedback_val = first_row.get('general_feedback', 'N/A')
            st.write(f"• General Feedback: `{feedback_val}`")
        
        # Prepare user ratings and cohort averages FIRST
        user_ratings = {
            'unit_culture_rating': unit_culture,
            'benefits_rating': benefits,
            'growth_opportunities_rating': growth,
            'hospital_quality_rating': hospital_quality,
            'general_feedback': general_feedback.strip()
        }
        
        cohort_averages = {
            'unit_culture_rating': 3.5,
            'benefits_rating': 3.2,
            'growth_opportunities_rating': 3.1,
            'hospital_quality_rating': 3.6
        }
        
        # Build and show prompt
        system_prompt = AI_MODELS["culture_analysis"]["system_prompt"]
        prompt, _ = self.insight_service.build_culture_analysis_prompt(user_ratings, cohort_averages)
        DataDisplay.show_prompt_and_system(prompt, system_prompt)
        
        # Check existing insight
        DataDisplay.show_existing_insight_status(
            self.data['ai_insights_df'], self.selected_user_id, "Culture Analysis"
        )
        
        # Generate button
        if st.button("🚀 Generate Culture Analysis", type="primary", use_container_width=True):
            try:
                with st.spinner("Generating..."):
                    content, prompt_used, ratings_used = self.insight_service.generate_culture_analysis(
                        user_ratings, cohort_averages, model, temperature, max_tokens
                    )
                    
                    if content and not content.startswith("Error:"):
                        st.subheader("✨ Generated Result:")
                        st.success(content)
                        st.caption("💡 Generation successful")
                    else:
                        st.error(content or "Generation failed")
                        
            except Exception as e:
                st.error(f"Error during generation: {str(e)}")

class SkillTransferView:
    """View component for Skill Transfer insight"""
    
    def __init__(self, insight_service, data, selected_user_id, user_data):
        self.insight_service = insight_service
        self.data = data
        self.selected_user_id = selected_user_id
        self.user_data = user_data
    
    def render(self):
        # Show user info
        DataDisplay.show_user_header(self.user_data, self.selected_user_id)
        
        if self.user_data.empty:
            st.warning("No user data available")
            return
        
        first_row = self.user_data.iloc[0]
        current_specialty = first_row.get('specialty')
        current_pay = first_row.get('base_pay')
        
        if not current_specialty or not current_pay:
            st.warning("Missing specialty or pay data for skill transfer analysis")
            return
        
        # Parameters
        param_controls = ParameterControls("Skill Transfer")
        model, temperature, max_tokens = param_controls.render()
        
        # Current user data
        st.subheader("📊 Current User Data")
        curr_col1, curr_col2 = st.columns(2)
        
        with curr_col1:
            st.write(f"**Current Specialty:** `{current_specialty}`")
            st.write(f"**Current Base Pay:** `${current_pay}/hr`")
        
        with curr_col2:
            years_group = first_row.get('total_years_of_experience_group', 'N/A')
            state = first_row.get('state', 'N/A')
            st.write(f"**Experience Group:** `{years_group}`")
            st.write(f"**State:** `{state}`")
        
        # Show skill transfer analysis
        st.subheader("🔍 Skill Transfer Analysis")
        
        error_msg, transfer_options = self.insight_service.compute_skill_transfer_options(
            current_specialty, current_pay, years_group, state,
            self.data['skills_df'], self.data['avg_pay_df']
        )
        
        if error_msg:
            st.warning(error_msg)
            return
        
        if transfer_options.empty:
            st.info("No higher-paying specialties found with skill overlap")
            return
        
        st.write("**Top Transfer Options Found:**")
        
        for i, (_, row) in enumerate(transfer_options.iterrows(), 1):
            transfer_col1, transfer_col2, transfer_col3 = st.columns(3)
            
            with transfer_col1:
                st.write(f"**Option {i}: {row['specialty_2']}**")
                st.write(f"• Pay Increase: `+${row['pay_increase']:.0f}/hr`")
                
            with transfer_col2:
                st.write(f"**Avg Pay: `${row['avg_base_pay']:.0f}/hr`**")
                st.write(f"• Overlap: `{row['overlap_percentage']:.1f}%`")
                
            with transfer_col3:
                skills = row.get('shared_skill_names', '')
                if isinstance(skills, str) and skills.startswith('['):
                    try:
                        skills = eval(skills)
                        skills_text = ', '.join(skills[:2]) if isinstance(skills, list) else skills
                    except:
                        skills_text = skills
                else:
                    skills_text = str(skills)
                st.write(f"**Key Skills:**")
                st.write(f"• `{skills_text}`")
        
        # Build raw bullets for prompt
        raw_bullets = []
        for _, row in transfer_options.iterrows():
            increase = row['pay_increase']
            specialty = row['specialty_2']
            raw_bullets.append(f"• {specialty}: +${increase:.0f}/hr potential increase")
        
        # Build and show prompt
        system_prompt = AI_MODELS["skill_transfer"]["system_prompt"]
        prompt = self.insight_service.build_skill_transfer_prompt(current_specialty, raw_bullets)
        DataDisplay.show_prompt_and_system(prompt, system_prompt)
        
        # Check existing insight
        DataDisplay.show_existing_insight_status(
            self.data['ai_insights_df'], self.selected_user_id, "Skill Transfer"
        )
        
        # Generate button
        if st.button("🚀 Generate Skill Transfer Suggestions", type="primary", use_container_width=True):
            try:
                with st.spinner("Generating..."):
                    suggestions, prompt_used = self.insight_service.generate_skill_transfer_suggestions(
                        current_specialty, raw_bullets, model, temperature, max_tokens
                    )
                    
                    if suggestions and not str(suggestions[0]).startswith("Error:"):
                        st.subheader("✨ Generated Suggestions:")
                        for suggestion in suggestions:
                            st.success(suggestion)
                        st.caption("💡 Generation successful")
                    else:
                        st.error("Generation failed or returned errors")
                        
            except Exception as e:
                st.error(f"Error during generation: {str(e)}")