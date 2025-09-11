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
            
            # Compact row layout
            row_col1, row_col2, row_col3, row_col4 = st.columns([0.5, 2, 1, 1])
            
            with row_col1:
                st.write(f"**{idx}**")
            
            with row_col2:
                st.write(f"**{insight_type}** - {user_name}")
                # Truncated content preview
                content = row['content']
                preview = content[:100] + "..." if len(content) > 100 else content
                st.write(f"`{preview}`")
            
            with row_col3:
                st.write(f"**{user_specialty}**")
                st.write(f"{date_str}")
            
            with row_col4:
                if st.button("View", key=f"view_{idx}"):
                    st.session_state[f"show_detail_{idx}"] = not st.session_state.get(f"show_detail_{idx}", False)
            
            # Show full content if requested
            if st.session_state.get(f"show_detail_{idx}", False):
                with st.container():
                    st.write("**Full Content:**")
                    st.success(content)
                    
                    # Quick details in two columns
                    detail_col1, detail_col2 = st.columns(2)
                    with detail_col1:
                        st.write(f"User ID: `{row['user_id']}`")
                        st.write(f"Email: {row.get('email', 'N/A')}")
                    with detail_col2:
                        if not self.nursing_df.empty:
                            user_rows = self.nursing_df[self.nursing_df['user_id'] == row['user_id']]
                            if not user_rows.empty:
                                first_user_row = user_rows.iloc[0]
                                st.write(f"Experience: {first_user_row.get('total_years_of_experience', 'N/A')} years")
                                st.write(f"Base Pay: ${first_user_row.get('base_pay', 'N/A')}/hr")
            
            st.divider()