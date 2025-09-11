import streamlit as st
import pandas as pd
from datetime import datetime

class ResultsSummaryView:
    """View component for Results Summary - shows all saved AI insights"""
    
    def __init__(self, data):
        self.data = data
        self.ai_insights_df = data['ai_insights_df']
        self.nursing_df = data['nursing_df']
    
    def render(self):
        st.header("Results Summary")
        st.caption("All saved AI insights - simplified view")
        
        if self.ai_insights_df.empty:
            st.info("No AI insights found in the database")
            return
        
        # Simple filters in one row
        col1, col2, col3 = st.columns(3)
        
        with col1:
            insight_types = ["All"] + sorted(self.ai_insights_df['summary_type'].unique().tolist())
            selected_type = st.selectbox("Type", insight_types)
        
        with col2:
            sort_options = ["Newest First", "Oldest First", "By Type"]
            selected_sort = st.selectbox("Sort", sort_options)
        
        with col3:
            st.metric("Total Results", len(self.ai_insights_df))
        
        # Filter data
        filtered_df = self.ai_insights_df.copy()
        if selected_type != "All":
            filtered_df = filtered_df[filtered_df['summary_type'] == selected_type]
        
        # Sort data
        if selected_sort == "Newest First":
            filtered_df = filtered_df.sort_values('created_at', ascending=False)
        elif selected_sort == "Oldest First":
            filtered_df = filtered_df.sort_values('created_at', ascending=True)
        elif selected_sort == "By Type":
            filtered_df = filtered_df.sort_values(['summary_type', 'created_at'], ascending=[True, False])
        
        if filtered_df.empty:
            st.info("No results match the current filters")
            return
        
        st.divider()
        
        # Compact table view
        for idx, (_, row) in enumerate(filtered_df.iterrows(), 1):
            
            # Get user info
            user_name = f"{row.get('first_name', 'No First')} {row.get('last_name', 'No Last')}"
            insight_type = row['summary_type'].replace('_', ' ').title()
            
            # Format date
            created_date = row['created_at']
            if isinstance(created_date, str):
                try:
                    created_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                except:
                    pass
            date_str = created_date.strftime("%m/%d %H:%M") if hasattr(created_date, 'strftime') else str(created_date)[:10]
            
            # Get user specialty
            user_specialty = "N/A"
            if not self.nursing_df.empty:
                user_rows = self.nursing_df[self.nursing_df['user_id'] == row['user_id']]
                if not user_rows.empty:
                    user_specialty = user_rows.iloc[0].get('specialty', 'N/A')
            
            # Header row with metadata
            header_col1, header_col2, header_col3 = st.columns([2, 1, 1])
            
            with header_col1:
                st.write(f"**{idx}. {insight_type}** - {user_name}")
            
            with header_col2:
                st.write(f"**{user_specialty}** | {date_str}")
            
            with header_col3:
                if st.button("Details", key=f"details_{idx}"):
                    st.session_state[f"show_detail_{idx}"] = not st.session_state.get(f"show_detail_{idx}", False)
            
            # Show full AI content by default
            content = row['content']
            st.success(content)
            
            # Show additional details if requested
            if st.session_state.get(f"show_detail_{idx}", False):
                with st.container():
                    st.write("**Additional User Details:**")
                    detail_col1, detail_col2 = st.columns(2)
                    
                    with detail_col1:
                        st.write(f"User ID: `{row['user_id']}`")
                        st.write(f"Email: {row.get('email', 'N/A')}")
                        st.write(f"Content Length: {len(content)} characters")
                    
                    with detail_col2:
                        if not self.nursing_df.empty:
                            user_rows = self.nursing_df[self.nursing_df['user_id'] == row['user_id']]
                            if not user_rows.empty:
                                first_user_row = user_rows.iloc[0]
                                st.write(f"Degree: {first_user_row.get('nursing_degree', 'N/A')}")
                                st.write(f"Experience: {first_user_row.get('total_years_of_experience', 'N/A')} years")
                                st.write(f"Base Pay: ${first_user_row.get('base_pay', 'N/A')}/hr")
                            else:
                                st.write("No additional user data found")
                        else:
                            st.write("No user data available")
            
            st.divider()