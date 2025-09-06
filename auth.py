import streamlit as st
import hashlib

def check_password():
    """Returns True if the user has entered the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        password_hash = hashlib.sha256(st.session_state["password"].encode()).hexdigest()
        
        # Replace this with your actual password hash
        # To generate: hashlib.sha256("your_password".encode()).hexdigest()
        correct_password_hash = st.secrets.get("APP_PASSWORD_HASH")
        correct_password_hash = "c685b82fa8d9efb3fc52b5c9781930b6a4dba2835234cc9882c669445438ac9c"
        
        if password_hash == correct_password_hash:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    # Return True if password is correct
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password
    st.markdown("### 🔐 Access Required")
    st.markdown("This app uses OpenAI API calls. Please enter the access password:")
    
    st.text_input(
        "Password", 
        type="password", 
        on_change=password_entered, 
        key="password",
        placeholder="Enter password to continue..."
    )
    
    if "password_correct" in st.session_state:
        if not st.session_state["password_correct"]:
            st.error("😞 Password incorrect. Please try again.")
    
    return False

def logout():
    """Clear password session state"""
    if "password_correct" in st.session_state:
        del st.session_state["password_correct"]
    st.rerun()
