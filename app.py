import streamlit as st
import os
from utils.pdf_processor import PDFProcessor
from utils.groq_client import GroqClient
from utils.content_generator import ContentGenerator
from utils.storage_manager import StorageManager

def main():
    st.set_page_config(page_title="AI Study Platform", layout="wide")
    
    # Initialize session state
    if 'current_course' not in st.session_state:
        st.session_state.current_course = None
    if 'current_slide' not in st.session_state:
        st.session_state.current_slide = 0
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    
    # Sidebar for navigation
    st.sidebar.title("📚 AI Study Platform")
    
    # API Configuration
    with st.sidebar.expander("🔑 API Configuration"):
        groq_api_key = st.text_input("Groq API Key", type="password")
        google_api_key = st.text_input("Google API Key (for images)", type="password")
        cse_id = st.text_input("Google CSE ID")
    
    # Main navigation
    menu = st.sidebar.radio("Navigation", 
                           ["🏠 Home", "📖 Study", "💬 Chat Assistant", "📊 Progress"])
    
    if menu == "🏠 Home":
        show_home_page()
    elif menu == "📖 Study":
        if st.session_state.current_course:
            show_study_interface()
        else:
            st.warning("Please load or create a course first")
    elif menu == "💬 Chat Assistant":
        show_chat_interface()
    elif menu == "📊 Progress":
        show_progress_page()

def show_home_page():
    st.title("🎓 AI-Powered Study Platform")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📤 Create New Course")
        pdf_file = st.file_uploader("Upload PDF", type=['pdf'])
        if pdf_file and st.button("Generate Course"):
            with st.spinner("Analyzing PDF and generating course..."):
                create_new_course(pdf_file)
    
    with col2:
        st.subheader("📂 Load Existing Course")
        uploaded_json = st.file_uploader("Upload Course JSON", type=['json'])
        if uploaded_json and st.button("Load Course"):
            load_existing_course(uploaded_json)

def show_study_interface():
    course = st.session_state.current_course
    current_slide_idx = st.session_state.current_slide
    
    # Sidebar TOC
    st.sidebar.subheader("Table of Contents")
    for i, section in enumerate(course['toc']):
        if st.sidebar.button(f"{i+1}. {section['title']}", key=f"toc_{i}"):
            st.session_state.current_slide = section['start_slide']
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        display_slide_content(current_slide_idx)
        
        # Navigation buttons
        col_prev, col_next, col_check = st.columns([1, 1, 2])
        with col_prev:
            if st.button("⬅️ Previous") and current_slide_idx > 0:
                st.session_state.current_slide -= 1
                st.rerun()
        with col_next:
            if st.button("Next ➡️") and current_slide_idx < len(course['slides']) - 1:
                st.session_state.current_slide += 1
                st.rerun()
        with col_check:
            # Check if current slide has quiz
            current_slide = course['slides'][current_slide_idx]
            if 'quiz' in current_slide:
                if st.button("✅ Check Answer"):
                    evaluate_answer(current_slide_idx)
    
    with col2:
        show_quiz_interface(current_slide_idx)
        show_bookmarks()

def display_slide_content(slide_idx):
    slide = st.session_state.current_course['slides'][slide_idx]
    
    st.markdown(f"## {slide['title']}")
    st.markdown(slide['content'])
    
    if slide.get('image_path') and os.path.exists(slide['image_path']):
        st.image(slide['image_path'])
    
    # Bookmark button
    if st.button("🔖 Bookmark This Slide"):
        add_bookmark(slide_idx)

def show_quiz_interface(slide_idx):
    slide = st.session_state.current_course['slides'][slide_idx]
    
    if 'quiz' in slide:
        quiz = slide['quiz']
        st.subheader("❓ Quiz")
        st.write(quiz['question'])
        
        if quiz['type'] == 'multiple_choice':
            options = quiz['options']
            answer = st.radio("Select answer:", options, key=f"quiz_{slide_idx}")
            st.session_state.user_answers[slide_idx] = answer
            
        elif quiz['type'] == 'short_answer':
            answer = st.text_area("Your answer:", key=f"quiz_{slide_idx}")
            st.session_state.user_answers[slide_idx] = answer

# Additional functions for chat, progress, etc.
