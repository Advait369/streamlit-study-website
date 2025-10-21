# app.py
import streamlit as st
import time
from utils.pdf_processor import PDFProcessor
from utils.groq_client import GroqClient
from utils.content_generator import ContentGenerator
from utils.storage_manager import StorageManager

def main():
    st.set_page_config(
        page_title="QuickStudy AI", 
        page_icon="🚀",
        layout="wide"
    )
    
    # Apply custom CSS for better UI
    apply_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Main app flow
    show_sidebar()
    
    if st.session_state.current_view == "home":
        show_home_page()
    elif st.session_state.current_view == "study":
        show_study_interface()
    elif st.session_state.current_view == "chat":
        show_chat_interface()
    elif st.session_state.current_view == "progress":
        show_progress_page()

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'current_course': None,
        'current_slide': 0,
        'user_answers': {},
        'bookmarks': [],
        'chat_history': [],
        'current_view': 'home',
        'user_id': str(hash(str(time.time())))[:8]  # Simple session-based ID
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def apply_custom_css():
    """Apply custom CSS for better styling"""
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .slide-card {
        padding: 2rem;
        border-radius: 10px;
        border-left: 5px solid #1E88E5;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
    }
    .quiz-box {
        background-color: #e3f2fd;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .progress-bar {
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def show_sidebar():
    """Sidebar navigation and course info"""
    with st.sidebar:
        st.title("🚀 QuickStudy AI")
        st.markdown("---")
        
        # API Configuration (collapsible)
        with st.expander("🔧 Setup API Keys", expanded=False):
            groq_api_key = st.text_input("Groq API Key", type="password", 
                                       help="Get free API key from Groq Cloud")
            google_api_key = st.text_input("Google API Key", type="password",
                                         help="For image search (optional)")
            cse_id = st.text_input("Google CSE ID", 
                                 help="Custom Search Engine ID for images")
            
            if groq_api_key:
                st.session_state.groq_api_key = groq_api_key
            if google_api_key:
                st.session_state.google_api_key = google_api_key
            if cse_id:
                st.session_state.cse_id = cse_id
        
        st.markdown("---")
        
        # Navigation
        nav_options = {
            "🏠 Create/Load Course": "home",
            "📖 Study": "study", 
            "💬 Ask Questions": "chat",
            "📊 My Progress": "progress"
        }
        
        for label, view in nav_options.items():
            if st.button(label, use_container_width=True):
                st.session_state.current_view = view
                st.rerun()
        
        # Current course info
        if st.session_state.current_course:
            st.markdown("---")
            st.subheader("Current Course")
            course = st.session_state.current_course
            st.write(f"**{course['original_pdf_name']}**")
            st.write(f"📚 {len(course['slides'])} slides")
            st.write(f"🎯 {course['processing_metadata']['difficulty_level']}")
            
            # Progress
            progress = len(st.session_state.user_answers) / len(course['slides'])
            st.progress(progress)
            st.write(f"Progress: {int(progress * 100)}%")

def show_home_page():
    """Home page with course creation and loading"""
    st.markdown('<div class="main-header">🚀 QuickStudy AI</div>', 
                unsafe_allow_html=True)
    st.markdown("Transform any PDF into an interactive study session in seconds!")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📤 Create New Course")
        
        pdf_file = st.file_uploader("Upload PDF", type=['pdf'], 
                                   help="Upload any educational PDF")
        
        user_prompt = st.text_area(
            "How should I prepare this material?",
            placeholder="Examples: 'Make it simple and easy to understand', 'Create a quick study session', 'Focus on key concepts only', 'Prepare for exam preparation'",
            help="Tell the AI how to structure your study material"
        )
        
        if st.button("🚀 Generate Study Course", type="primary", use_container_width=True):
            if not pdf_file:
                st.error("Please upload a PDF file")
            elif not st.session_state.get('groq_api_key'):
                st.error("Please enter your Groq API key in the sidebar")
            else:
                create_new_course(pdf_file, user_prompt)
    
    with col2:
        st.subheader("📂 Load Existing Course")
        
        uploaded_json = st.file_uploader("Upload Course File", type=['json'],
                                       help="Upload a previously generated .json course file")
        
        if uploaded_json and st.button("📖 Load Course", use_container_width=True):
            load_existing_course(uploaded_json)

def create_new_course(pdf_file, user_prompt):
    """Create a new course from PDF with progress tracking"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Process PDF
        status_text.text("📄 Analyzing PDF structure...")
        pdf_processor = PDFProcessor()
        pdf_text = pdf_processor.extract_text(pdf_file)
        course_id = pdf_processor.generate_file_hash(pdf_file)
        progress_bar.progress(20)
        
        # Step 2: Generate TOC
        status_text.text("📑 Creating table of contents...")
        groq_client = GroqClient(st.session_state.groq_api_key)
        toc = groq_client.generate_toc(pdf_text, user_prompt)
        progress_bar.progress(40)
        
        # Step 3: Generate content with progress for each section
        status_text.text("🎨 Creating study slides...")
        content_generator = ContentGenerator(groq_client)
        
        if st.session_state.get('google_api_key') and st.session_state.get('cse_id'):
            image_search = ImageSearch(st.session_state.google_api_key, st.session_state.cse_id)
        else:
            image_search = None
        
        all_slides = []
        total_sections = len(toc)
        
        for i, section in enumerate(toc):
            status_text.text(f"📝 Processing section {i+1} of {total_sections}: {section['title']}")
            section_slides = content_generator.generate_section_content(
                section, pdf_text, user_prompt, course_id, image_search
            )
            all_slides.extend(section_slides)
            progress_bar.progress(40 + (i + 1) * 50 / total_sections)
        
        # Step 4: Save course
        status_text.text("💾 Saving course...")
        course_data = {
            "course_id": course_id,
            "original_pdf_name": pdf_file.name,
            "user_prompt": user_prompt,
            "created_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "toc": toc,
            "slides": all_slides,
            "processing_metadata": {
                "total_sections": total_sections,
                "completion_time": "Quick study session",
                "difficulty_level": detect_difficulty_level(user_prompt)
            }
        }
        
        storage_manager = StorageManager()
        storage_manager.save_course(course_id, course_data)
        
        # Load into session
        st.session_state.current_course = course_data
        st.session_state.current_view = "study"
        st.session_state.current_slide = 0
        st.session_state.user_answers = {}
        st.session_state.bookmarks = []
        
        progress_bar.progress(100)
        status_text.text("✅ Course ready! Redirecting to study...")
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"Error creating course: {str(e)}")
        status_text.text("❌ Failed to create course")

def detect_difficulty_level(user_prompt):
    """Auto-detect difficulty level from user prompt"""
    prompt_lower = user_prompt.lower()
    if any(word in prompt_lower for word in ['simple', 'easy', 'basic', 'beginner']):
        return "Beginner"
    elif any(word in prompt_lower for word in ['quick', 'fast', 'overview']):
        return "Quick Overview"
    elif any(word in prompt_lower for word in ['detailed', 'comprehensive', 'advanced']):
        return "Advanced"
    else:
        return "Standard"

def show_study_interface():
    """Main study interface with slides and quizzes"""
    course = st.session_state.current_course
    current_slide_idx = st.session_state.current_slide
    current_slide = course['slides'][current_slide_idx]
    
    # Sidebar TOC
    with st.sidebar:
        st.subheader("📑 Table of Contents")
        for i, section in enumerate(course['toc']):
            if st.button(f"{i+1}. {section['title']}", key=f"toc_{i}", 
                        use_container_width=True):
                st.session_state.current_slide = section.get('start_slide', 0)
                st.rerun()
        
        # Bookmarks
        if st.session_state.bookmarks:
            st.subheader("🔖 Bookmarks")
            for bookmark_idx in st.session_state.bookmarks:
                slide_title = course['slides'][bookmark_idx]['title']
                if st.button(f"📍 {slide_title[:30]}...", key=f"bm_{bookmark_idx}"):
                    st.session_state.current_slide = bookmark_idx
                    st.rerun()
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Slide content
        st.markdown(f'<div class="slide-card">', unsafe_allow_html=True)
        st.markdown(f"## {current_slide['title']}")
        st.markdown(current_slide['content'])
        
        if current_slide.get('image_path') and os.path.exists(current_slide['image_path']):
            st.image(current_slide['image_path'], use_column_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Navigation
        nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 2])
        with nav_col1:
            if st.button("⬅️ Previous", disabled=current_slide_idx == 0):
                st.session_state.current_slide -= 1
                st.rerun()
        with nav_col2:
            if st.button("Next ➡️", disabled=current_slide_idx == len(course['slides'])-1):
                st.session_state.current_slide += 1
                st.rerun()
        with nav_col3:
            if 'quiz' in current_slide:
                if st.button("✅ Check Answer", type="primary", use_container_width=True):
                    evaluate_answer(current_slide_idx)
            else:
                if st.button("🔖 Bookmark", use_container_width=True):
                    add_bookmark(current_slide_idx)
                    st.success("Slide bookmarked!")
    
    with col2:
        # Quiz section
        if 'quiz' in current_slide:
            show_quiz_interface(current_slide_idx)
        
        # Progress indicator
        st.markdown("---")
        st.write(f"**Slide {current_slide_idx + 1} of {len(course['slides'])}**")
        progress = (current_slide_idx + 1) / len(course['slides'])
        st.progress(progress)

def show_quiz_interface(slide_idx):
    """Display and handle quizzes"""
    slide = st.session_state.current_course['slides'][slide_idx]
    quiz = slide['quiz']
    
    st.markdown('<div class="quiz-box">', unsafe_allow_html=True)
    st.subheader("❓ Quick Check")
    st.write(quiz['question'])
    
    user_answer_key = f"quiz_{slide_idx}"
    
    if quiz['type'] == 'multiple_choice':
        options = quiz['options']
        user_answer = st.radio("Select your answer:", options, key=user_answer_key)
        st.session_state.user_answers[slide_idx] = user_answer
        
    elif quiz['type'] == 'multi_select':
        options = quiz['options']
        user_answer = st.multiselect("Select all that apply:", options, key=user_answer_key)
        st.session_state.user_answers[slide_idx] = user_answer
        
    elif quiz['type'] == 'short_answer':
        user_answer = st.text_area("Your answer:", key=user_answer_key, height=100)
        st.session_state.user_answers[slide_idx] = user_answer
    
    st.markdown('</div>', unsafe_allow_html=True)

def evaluate_answer(slide_idx):
    """Evaluate quiz answer using AI"""
    slide = st.session_state.current_course['slides'][slide_idx]
    quiz = slide['quiz']
    user_answer = st.session_state.user_answers.get(slide_idx)
    
    if not user_answer:
        st.warning("Please provide an answer first")
        return
    
    with st.spinner("🤔 Evaluating your answer..."):
        evaluator = QuizEvaluator(st.session_state.groq_client)
        result = evaluator.evaluate_answer(user_answer, quiz, slide['title'])
        
        # Show results
        if quiz['type'] in ['multiple_choice', 'multi_select']:
            if result['is_correct']:
                st.success("✅ Correct! Well done!")
            else:
                st.error("❌ Not quite right. Keep learning!")
                st.info(f"**Correct answer:** {quiz['correct_answer']}")
        else:  # short answer
            st.info(f"**Score:** {result['score']}/10")
            st.write(f"**Feedback:** {result['feedback']}")
        
        # Save progress
        save_user_progress()

# Additional utility functions (add_bookmark, save_user_progress, etc.)
# ... [Previous implementation details] ...
