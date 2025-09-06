import pandas as pd
import streamlit as st
from typing import Optional, Dict, Any

def clean_text_value(value: Any) -> str:
    """
    Clean and standardize text values from database.
    
    Args:
        value: Raw value from database
        
    Returns:
        str: Cleaned text or 'N/A' if empty/null
    """
    if value is None or pd.isna(value):
        return 'N/A'
    
    text = str(value).strip()
    return text if text else 'N/A'

def format_currency(amount: Optional[float], prefix: str = '$', suffix: str = '/hr') -> str:
    """
    Format currency values consistently.
    
    Args:
        amount: Numeric amount to format
        prefix: Currency symbol
        suffix: Unit suffix
        
    Returns:
        str: Formatted currency string
    """
    if amount is None or pd.isna(amount):
        return 'N/A'
    
    try:
        return f"{prefix}{float(amount):.0f}{suffix}"
    except (ValueError, TypeError):
        return 'N/A'

def format_location(city: Optional[str], state: Optional[str]) -> str:
    """
    Format city, state location consistently.
    
    Args:
        city: City name
        state: State name
        
    Returns:
        str: Formatted location string
    """
    clean_city = clean_text_value(city)
    clean_state = clean_text_value(state)
    
    if clean_city == 'N/A' and clean_state == 'N/A':
        return 'N/A'
    elif clean_city == 'N/A':
        return clean_state
    elif clean_state == 'N/A':
        return clean_city
    else:
        return f"{clean_city}, {clean_state}"

def safe_eval_list(value: Any) -> list:
    """
    Safely evaluate string representations of lists.
    
    Args:
        value: Value that might be a string representation of a list
        
    Returns:
        list: Parsed list or empty list if parsing fails
    """
    if isinstance(value, list):
        return value
    
    if isinstance(value, str) and value.startswith('['):
        try:
            return eval(value)
        except (SyntaxError, NameError, ValueError):
            return []
    
    return []

def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to specified length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        suffix: Suffix to add when truncated
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def calculate_completeness_score(row: pd.Series, important_columns: list) -> float:
    """
    Calculate data completeness score for a row.
    
    Args:
        row: Pandas Series representing a data row
        important_columns: List of column names to check
        
    Returns:
        float: Completeness score between 0 and 1
    """
    if not important_columns:
        return 1.0
    
    available_columns = [col for col in important_columns if col in row.index]
    if not available_columns:
        return 0.0
    
    non_null_count = sum(1 for col in available_columns if not pd.isna(row[col]))
    return non_null_count / len(available_columns)

def display_data_metrics(df: pd.DataFrame, title: str = "Data Metrics"):
    """
    Display basic data quality metrics in Streamlit.
    
    Args:
        df: DataFrame to analyze
        title: Title for the metrics display
    """
    if df.empty:
        st.warning(f"{title}: No data available")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Rows", f"{len(df):,}")
    
    with col2:
        st.metric("Columns", len(df.columns))
    
    with col3:
        missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        st.metric("Missing %", f"{missing_pct:.1f}%")
    
    with col4:
        unique_users = df['user_id'].nunique() if 'user_id' in df.columns else 'N/A'
        st.metric("Unique Users", unique_users)

def validate_required_columns(df: pd.DataFrame, required_columns: list, table_name: str = "DataFrame") -> bool:
    """
    Validate that DataFrame contains required columns.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        table_name: Name for error messaging
        
    Returns:
        bool: True if all required columns present
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"{table_name} missing required columns: {missing_columns}")
        return False
    
    return True

class DataValidator:
    """Class for validating data quality and structure"""
    
    @staticmethod
    def check_nursing_data(df: pd.DataFrame) -> Dict[str, Any]:
        """Validate nursing data structure and quality"""
        required_cols = ['user_id', 'specialty', 'base_pay']
        
        validation = {
            'has_required_columns': validate_required_columns(df, required_cols, "Nursing data"),
            'row_count': len(df),
            'user_count': df['user_id'].nunique() if 'user_id' in df.columns else 0,
            'missing_specialty_pct': (df['specialty'].isnull().sum() / len(df)) * 100 if 'specialty' in df.columns else 100,
            'missing_pay_pct': (df['base_pay'].isnull().sum() / len(df)) * 100 if 'base_pay' in df.columns else 100
        }
        
        return validation
    
    @staticmethod
    def check_skills_data(df: pd.DataFrame) -> Dict[str, Any]:
        """Validate skills overlap data structure and quality"""
        required_cols = ['specialty_1', 'specialty_2', 'overlap_percentage']
        
        validation = {
            'has_required_columns': validate_required_columns(df, required_cols, "Skills data"),
            'row_count': len(df),
            'unique_specialty_pairs': len(df[['specialty_1', 'specialty_2']].drop_duplicates()) if len(df) > 0 else 0,
            'avg_overlap': df['overlap_percentage'].mean() if 'overlap_percentage' in df.columns else 0
        }
        
        return validation