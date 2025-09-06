import tiktoken
import streamlit as st
from typing import Dict, Tuple

# OpenAI pricing as of 2024 (per 1M tokens)
OPENAI_PRICING = {
    "gpt-4o": {
        "input": 5.00,   # $5.00 per 1M input tokens
        "output": 15.00  # $15.00 per 1M output tokens
    },
    "gpt-4o-mini": {
        "input": 0.15,   # $0.15 per 1M input tokens  
        "output": 0.60   # $0.60 per 1M output tokens
    },
    "gpt-4": {
        "input": 30.00,  # $30.00 per 1M input tokens
        "output": 60.00  # $60.00 per 1M output tokens
    }
}

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    Count tokens in a text string using tiktoken.
    
    Args:
        text: Text to count tokens for
        model: Model name for tokenizer selection
        
    Returns:
        int: Number of tokens
    """
    try:
        # Map model names to tiktoken encodings
        encoding_map = {
            "gpt-4o": "cl100k_base",
            "gpt-4o-mini": "cl100k_base", 
            "gpt-4": "cl100k_base"
        }
        
        encoding_name = encoding_map.get(model, "cl100k_base")
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception as e:
        # Fallback: rough estimate of 4 characters per token
        return len(text) // 4

def calculate_prompt_cost(system_prompt: str, user_prompt: str, max_tokens: int, model: str) -> Dict[str, float]:
    """
    Calculate estimated cost for a single prompt.
    
    Args:
        system_prompt: System message content
        user_prompt: User message content  
        max_tokens: Maximum output tokens
        model: Model name
        
    Returns:
        dict: Cost breakdown with input_cost, output_cost, total_cost
    """
    if model not in OPENAI_PRICING:
        return {"input_cost": 0, "output_cost": 0, "total_cost": 0, "error": f"Unknown model: {model}"}
    
    # Count input tokens
    input_tokens = count_tokens(system_prompt, model) + count_tokens(user_prompt, model)
    
    # Calculate costs (pricing is per 1M tokens)
    input_cost = (input_tokens / 1_000_000) * OPENAI_PRICING[model]["input"]
    output_cost = (max_tokens / 1_000_000) * OPENAI_PRICING[model]["output"]
    total_cost = input_cost + output_cost
    
    return {
        "input_tokens": input_tokens,
        "max_output_tokens": max_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost, 
        "total_cost": total_cost
    }

def display_cost_breakdown(cost_data: Dict[str, float], title: str = "Cost Estimate"):
    """
    Display cost breakdown in Streamlit.
    
    Args:
        cost_data: Cost data from calculate_prompt_cost
        title: Title for the cost display
    """
    if "error" in cost_data:
        st.error(f"Cost calculation error: {cost_data['error']}")
        return
    
    st.subheader(f"💰 {title}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Input Tokens", 
            f"{cost_data['input_tokens']:,}",
            help="Number of tokens in system + user prompts"
        )
    
    with col2:
        st.metric(
            "Max Output", 
            f"{cost_data['max_output_tokens']:,}",
            help="Maximum tokens that could be generated"
        )
    
    with col3:
        st.metric(
            "Input Cost", 
            f"${cost_data['input_cost']:.4f}",
            help="Cost for processing the input prompt"
        )
    
    with col4:
        st.metric(
            "Max Total Cost", 
            f"${cost_data['total_cost']:.4f}",
            help="Maximum possible cost if full output is generated"
        )
    
    # Cost breakdown details
    with st.expander("💡 Cost Details"):
        st.write(f"**Input cost:** {cost_data['input_tokens']:,} tokens × ${OPENAI_PRICING.get('gpt-4o', {}).get('input', 0)/1_000_000:.6f} = ${cost_data['input_cost']:.4f}")
        st.write(f"**Output cost:** {cost_data['max_output_tokens']:,} tokens × ${OPENAI_PRICING.get('gpt-4o', {}).get('output', 0)/1_000_000:.6f} = ${cost_data['output_cost']:.4f}")
        st.write(f"**Total maximum:** ${cost_data['total_cost']:.4f}")
        st.caption("Actual cost may be lower if the response uses fewer than max_tokens")

class CostTracker:
    """Track cumulative costs across multiple API calls"""
    
    def __init__(self):
        if 'cost_tracker' not in st.session_state:
            st.session_state.cost_tracker = {
                'total_calls': 0,
                'total_cost': 0.0,
                'calls_by_type': {}
            }
    
    def add_call(self, insight_type: str, cost: float):
        """Add a new API call to the tracker"""
        st.session_state.cost_tracker['total_calls'] += 1
        st.session_state.cost_tracker['total_cost'] += cost
        
        if insight_type not in st.session_state.cost_tracker['calls_by_type']:
            st.session_state.cost_tracker['calls_by_type'][insight_type] = {'count': 0, 'cost': 0.0}
        
        st.session_state.cost_tracker['calls_by_type'][insight_type]['count'] += 1
        st.session_state.cost_tracker['calls_by_type'][insight_type]['cost'] += cost
    
    def display_session_summary(self):
        """Display session cost summary"""
        tracker = st.session_state.cost_tracker
        
        if tracker['total_calls'] == 0:
            st.info("No API calls made this session")
            return
        
        st.subheader("📊 Session Cost Summary")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total API Calls", tracker['total_calls'])
        with col2:
            st.metric("Total Session Cost", f"${tracker['total_cost']:.4f}")
        
        if tracker['calls_by_type']:
            st.write("**Breakdown by Insight Type:**")
            for insight_type, data in tracker['calls_by_type'].items():
                st.write(f"• {insight_type}: {data['count']} calls, ${data['cost']:.4f}")
    
    def reset(self):
        """Reset the cost tracker"""
        st.session_state.cost_tracker = {
            'total_calls': 0,
            'total_cost': 0.0,
            'calls_by_type': {}
        }

def update_pricing():
    """Function to update pricing when OpenAI changes rates"""
    st.warning("💡 Pricing shown is estimated based on OpenAI's published rates. Actual costs may vary.")
    st.caption("Last updated: January 2024. Check OpenAI's pricing page for current rates.")