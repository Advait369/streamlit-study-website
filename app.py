import streamlit as st
import time
import os
import json
import logging
from datetime import datetime

# Import utility modules
from utils.pdf_processor import PDFProcessor
from utils.groq_client import GroqClient
from utils.content_generator import ContentGenerator
from utils.image_search import ImageSearch
from utils.quiz_evaluator import QuizEvaluator
from utils.storage_manager import StorageManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="QuickStudy AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_custom_css():
    """Apply custom CSS styles"""
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 700;
    }
    .slide-card {
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid #1E88E5;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .quiz-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        border: 2px solid #90caf9;
    }
    .chat-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        height: 600px;
        overflow-y: auto;
    }
    .chat-message {
        padding: 0.8rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid;
    }
    .chat-user {
        background: #e3f2fd;
        border-left-color: #2196f3;
    }
    .chat-assistant {
        background: #f3e5f5;
        border-left-color: #9c27b0;
    }
    .toc-level-1 { font-weight: bold; font-size: 1.1em; margin-left: 0px; }
    .toc-level-2 { font-weight: 600; font-size: 1em; margin-left: 20px; }
    .toc-level-3 { font-weight: normal; font-size: 0.9em; margin-left: 40px; }
    </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'current_course': None,
        'current_slide': 0,
        'user_answers': {},
        'bookmarks': [],
        'chat_history': [],
        'current_view': 'home',
        'user_id': str(hash(str(time.time())))[:8],
        'groq_client': None,
        'storage_manager': StorageManager(),
        'last_course_loaded': None,
        'chat_input': ""  # New: track chat input separately
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def show_sidebar():
    """Main sidebar navigation"""
    with st.sidebar:
        st.title("🚀 QuickStudy AI")
        st.markdown("---")
        
        # API Configuration
        with st.expander("🔧 API Setup", expanded=False):
            groq_api_key = st.text_input(
                "Groq API Key", 
                type="password",
                help="Get free API key from Groq Cloud"
            )
            google_api_key = st.text_input(
                "Google API Key", 
                type="password",
                help="For image search (optional)"
            )
            cse_id = st.text_input(
                "Google CSE ID", 
                help="Custom Search Engine ID for images"
            )
            
            if groq_api_key:
                st.session_state.groq_api_key = groq_api_key
                try:
                    st.session_state.groq_client = GroqClient(groq_api_key)
                    st.success("✅ Groq API connected")
                except Exception as e:
                    st.error(f"❌ Groq API error: {str(e)}")
        
        st.markdown("---")
        
        # Navigation
        st.subheader("📚 Navigation")
        nav_options = {
            "🏠 Create/Load Course": "home",
            "📖 Study": "study", 
            "📊 My Progress": "progress"
        }
        
        for label, view in nav_options.items():
            if st.button(label, use_container_width=True, key=f"nav_{view}"):
                st.session_state.current_view = view
                st.rerun()
        
        # Current course info
        if st.session_state.current_course:
            st.markdown("---")
            st.subheader("📖 Current Course")
            course = st.session_state.current_course
            st.write(f"**{course['original_pdf_name']}**")
            st.write(f"📚 {len(course['slides'])} slides")
            
            progress = len(st.session_state.user_answers) / max(len(course['slides']), 1)
            st.progress(progress)
            st.write(f"Progress: {int(progress * 100)}%")

def show_home_page():
    """Home page with course creation and loading"""
    st.markdown('<div class="main-header">🚀 QuickStudy AI</div>', unsafe_allow_html=True)
    st.markdown("### Transform any PDF into an interactive study session in seconds!")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        show_course_creation()
    
    with col2:
        show_course_loading()

def show_course_creation():
    """Course creation section"""
    st.subheader("📤 Create New Course")
    
    pdf_file = st.file_uploader(
        "Upload PDF", 
        type=['pdf'],
        help="Upload any educational PDF document"
    )
    
    user_prompt = st.text_area(
        "How should I prepare this material?",
        placeholder="Examples: 'Make it simple and easy to understand', 'Create a quick study session', 'Focus on key concepts only', 'Prepare for exam preparation'",
        help="Tell the AI how to structure your study material",
        height=100
    )
    
    with st.expander("⚙️ Advanced Options"):
        enable_images = st.checkbox("Enable Image Search", value=True, 
                                  help="Search and add relevant images (requires Google API)")
    
    if st.button("🚀 Generate Study Course", type="primary", use_container_width=True):
        if not pdf_file:
            st.error("📄 Please upload a PDF file")
        elif not st.session_state.get('groq_api_key'):
            st.error("🔑 Please enter your Groq API key in the sidebar")
        else:
            create_new_course(pdf_file, user_prompt, enable_images)

def show_course_loading():
    """Course loading section"""
    st.subheader("📂 Load Existing Course")
    
    uploaded_json = st.file_uploader(
        "Upload Course File", 
        type=['json'],
        help="Upload a previously generated .json course file"
    )
    
    if uploaded_json and st.button("📖 Load Uploaded Course", use_container_width=True):
        load_course_from_file(uploaded_json)
    
    st.markdown("---")
    st.subheader("📚 My Recent Courses")
    
    user_courses = st.session_state.storage_manager.list_user_courses(st.session_state.user_id)
    
    if not user_courses:
        st.info("No recent courses found. Create your first course!")
    else:
        for course_info in user_courses[:5]:
            course_data = course_info['course_data']
            progress = course_info['progress']
            
            completion = len(progress.get('quiz_answers', {})) / max(len(course_data.get('slides', [])), 1)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{course_data['original_pdf_name']}**")
                st.write(f"{len(course_data['slides'])} slides • {int(completion * 100)}% complete")
            with col2:
                if st.button("📖", key=f"load_{course_info['course_id']}"):
                    load_existing_course(course_info['course_id'])

def create_new_course(pdf_file, user_prompt, enable_images):
    """Create a new course from PDF"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        pdf_processor = PDFProcessor()
        groq_client = GroqClient(st.session_state.groq_api_key)
        
        status_text.text("📄 Analyzing PDF structure...")
        pdf_text, pdf_metadata = pdf_processor.extract_text(pdf_file)
        course_id = pdf_processor.generate_file_hash(pdf_file)
        progress_bar.progress(10)
        
        # Check if course already exists
        existing_course = st.session_state.storage_manager.load_course(course_id)
        if existing_course:
            st.info("📚 Course already exists! Loading from cache...")
            st.session_state.current_course = existing_course
            st.session_state.current_view = "study"
            st.rerun()
            return
        
        status_text.text("📑 Creating table of contents...")
        toc = groq_client.generate_toc(pdf_text, user_prompt)
        progress_bar.progress(30)
        
        image_search = None
        if enable_images and st.session_state.get('google_api_key') and st.session_state.get('cse_id'):
            image_search = ImageSearch(st.session_state.google_api_key, st.session_state.cse_id)
        
        status_text.text("🎨 Creating study slides...")
        content_generator = ContentGenerator(groq_client)
        
        all_slides = content_generator.generate_course_content(
            toc, pdf_text, user_prompt, course_id, image_search
        )
        progress_bar.progress(80)
        
        status_text.text("💾 Saving course...")
        course_data = {
            "course_id": course_id,
            "original_pdf_name": pdf_file.name,
            "user_prompt": user_prompt,
            "created_date": datetime.now().isoformat(),
            "toc": toc,
            "slides": all_slides,
            "pdf_metadata": pdf_metadata,
            "processing_metadata": {
                "total_sections": len(toc),
                "total_slides": len(all_slides),
                "difficulty_level": detect_difficulty_level(user_prompt),
                "has_images": any(slide.get('image_path') for slide in all_slides)
            }
        }
        
        st.session_state.storage_manager.save_course(course_id, course_data)
        st.session_state.current_course = course_data
        st.session_state.current_view = "study"
        st.session_state.current_slide = 0
        st.session_state.user_answers = {}
        st.session_state.bookmarks = []
        
        progress_bar.progress(100)
        status_text.text("✅ Course ready! Redirecting...")
        time.sleep(2)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error creating course: {str(e)}")
        logger.error(f"Course creation failed: {str(e)}")

def detect_difficulty_level(user_prompt):
    """Auto-detect difficulty level from user prompt"""
    prompt_lower = user_prompt.lower()
    if any(word in prompt_lower for word in ['simple', 'easy', 'basic', 'beginner', 'intro']):
        return "Beginner Friendly"
    elif any(word in prompt_lower for word in ['quick', 'fast', 'overview', 'summary']):
        return "Quick Overview"
    elif any(word in prompt_lower for word in ['detailed', 'comprehensive', 'advanced', 'deep']):
        return "Advanced Level"
    elif any(word in prompt_lower for word in ['exam', 'test', 'assessment', 'practice']):
        return "Exam Preparation"
    else:
        return "Standard Level"

def load_course_from_file(uploaded_json):
    """Load course from uploaded JSON file"""
    try:
        course_data = json.load(uploaded_json)
        required_fields = ['course_id', 'slides', 'toc']
        if all(field in course_data for field in required_fields):
            st.session_state.current_course = course_data
            st.session_state.current_slide = 0
            st.session_state.current_view = "study"
            
            progress = st.session_state.storage_manager.load_user_progress(
                course_data['course_id'], 
                st.session_state.user_id
            )
            st.session_state.user_answers = progress.get('quiz_answers', {})
            st.session_state.bookmarks = progress.get('bookmarks', [])
            
            st.success(f"✅ Course loaded: {course_data['original_pdf_name']}")
            st.rerun()
        else:
            st.error("❌ Invalid course file format")
    except Exception as e:
        st.error(f"❌ Failed to load course: {str(e)}")

def load_existing_course(course_id):
    """Load existing course from storage"""
    course_data = st.session_state.storage_manager.load_course(course_id)
    if course_data:
        st.session_state.current_course = course_data
        st.session_state.current_slide = 0
        st.session_state.current_view = "study"
        
        progress = st.session_state.storage_manager.load_user_progress(
            course_id, 
            st.session_state.user_id
        )
        st.session_state.user_answers = progress.get('quiz_answers', {})
        st.session_state.bookmarks = progress.get('bookmarks', [])
        st.session_state.current_slide = progress.get('current_slide', 0)
        
        st.success(f"✅ Course loaded: {course_data['original_pdf_name']}")
        st.rerun()
    else:
        st.error("❌ Course not found")

def show_study_interface():
    """Main study interface with new layout"""
    if not st.session_state.current_course:
        st.warning("📚 Please load a course first")
        st.session_state.current_view = "home"
        st.rerun()
        return
    
    # New layout: 1/4 left, 1/2 center, 1/4 right
    col_left, col_center, col_right = st.columns([1, 2, 1])
    
    with col_left:
        show_course_outline()
    
    with col_center:
        show_slide_content()
    
    with col_right:
        show_chat_interface()

def show_course_outline():
    """Show hierarchical course outline in left sidebar"""
    st.subheader("📑 Course Outline")
    
    course = st.session_state.current_course
    current_slide_idx = st.session_state.current_slide
    
    for section_idx, section in enumerate(course['toc']):
        # Level 1: Main sections
        is_current_section = (
            current_slide_idx >= section.get('start_slide', 0) and
            current_slide_idx < section.get('start_slide', 0) + section.get('estimated_slides', 3)
        )
        
        section_emoji = "📍" if is_current_section else "📖"
        if st.button(
            f"{section_emoji} {section['title']}", 
            key=f"section_{section_idx}",
            use_container_width=True
        ):
            st.session_state.current_slide = section.get('start_slide', 0)
            save_progress()
            st.rerun()
        
        # Level 2: Subtopics
        for subtopic_idx, subtopic in enumerate(section.get('subtopics', [])[:5]):  # Limit to 5 subtopics
            st.markdown(f'<div class="toc-level-2">• {subtopic}</div>', unsafe_allow_html=True)
            
            # Level 3: Key concepts (limited to 3 per subtopic)
            key_concepts = section.get('key_concepts', [])[subtopic_idx*3:(subtopic_idx+1)*3]
            for concept in key_concepts:
                st.markdown(f'<div class="toc-level-3">  ◦ {concept}</div>', unsafe_allow_html=True)
    
    # Bookmarks section
    if st.session_state.bookmarks:
        st.markdown("---")
        st.subheader("🔖 Bookmarks")
        for bookmark_idx in st.session_state.bookmarks:
            if bookmark_idx < len(course['slides']):
                slide_title = course['slides'][bookmark_idx]['title']
                if st.button(
                    f"📍 {slide_title[:25]}...", 
                    key=f"bm_{bookmark_idx}",
                    use_container_width=True
                ):
                    st.session_state.current_slide = bookmark_idx
                    save_progress()
                    st.rerun()

def show_slide_content():
    """Show slide content in center column"""
    course = st.session_state.current_course
    current_slide_idx = st.session_state.current_slide
    current_slide = course['slides'][current_slide_idx]
    
    # Display slide content
    st.markdown(f'<div class="slide-card">', unsafe_allow_html=True)
    st.markdown(f"### {current_slide['title']}")
    
    if current_slide.get('section_title'):
        st.caption(f"Section: {current_slide['section_title']}")
    
    st.markdown(current_slide['content'])
    
    # Key points
    if current_slide.get('key_points'):
        st.markdown("**Key Points:**")
        for point in current_slide['key_points']:
            st.markdown(f"- {point}")
    
    # Image
    if current_slide.get('image_path') and os.path.exists(current_slide['image_path']):
        st.image(current_slide['image_path'], use_column_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation and quiz controls
    show_slide_controls(current_slide_idx)

def show_slide_controls(current_slide_idx):
    """Show navigation and quiz controls"""
    course = st.session_state.current_course
    total_slides = len(course['slides'])
    current_slide = course['slides'][current_slide_idx]
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("⬅️ Previous", disabled=current_slide_idx == 0):
            st.session_state.current_slide = max(0, current_slide_idx - 1)
            save_progress()
            st.rerun()
    
    with col2:
        if st.button("Next ➡️", disabled=current_slide_idx == total_slides - 1):
            st.session_state.current_slide = min(total_slides - 1, current_slide_idx + 1)
            save_progress()
            st.rerun()
    
    with col3:
        if st.button("🔖 Bookmark", use_container_width=True):
            add_bookmark(current_slide_idx)
            st.success("📌 Slide bookmarked!")
    
    # Progress indicator
    progress = (current_slide_idx + 1) / total_slides
    st.progress(progress)
    st.write(f"**Slide {current_slide_idx + 1} of {total_slides}**")
    
    # Quiz section - ONLY show if current slide has a quiz
    if current_slide.get('quiz'):
        show_quiz_section(current_slide_idx)

def show_quiz_section(slide_idx):
    """Show quiz section only when there's a quiz"""
    st.markdown("---")
    st.markdown('<div class="quiz-box">', unsafe_allow_html=True)
    st.subheader("❓ Quick Check")
    
    slide = st.session_state.current_course['slides'][slide_idx]
    quiz = slide['quiz']
    
    # FIX: Check if quiz exists and has question
    if not quiz or not isinstance(quiz, dict) or 'question' not in quiz:
        st.warning("Quiz data is incomplete.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    st.write(quiz['question'])
    
    user_answer_key = f"quiz_{slide_idx}"
    
    if quiz['type'] == 'multiple_choice':
        options = quiz.get('options', [])
        if options:
            user_answer = st.radio("Select your answer:", options, key=user_answer_key)
            st.session_state.user_answers[slide_idx] = user_answer
        else:
            st.warning("No options available for this question.")
    
    elif quiz['type'] == 'multi_select':
        options = quiz.get('options', [])
        if options:
            user_answer = st.multiselect("Select all that apply:", options, key=user_answer_key)
            st.session_state.user_answers[slide_idx] = user_answer
        else:
            st.warning("No options available for this question.")
    
    elif quiz['type'] == 'short_answer':
        user_answer = st.text_area("Your answer:", key=user_answer_key, height=100)
        st.session_state.user_answers[slide_idx] = user_answer
    
    # Check answer button - ONLY for quizzes
    if st.button("✅ Check Answer", type="primary", use_container_width=True):
        evaluate_answer(slide_idx)
    
    # Show previous evaluation if exists
    if f"quiz_result_{slide_idx}" in st.session_state:
        show_quiz_result(slide_idx)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_chat_interface():
    """Show chat interface in right sidebar"""
    st.subheader("💬 Course Assistant")
    
    if not st.session_state.current_course:
        st.info("Please load a course first to ask questions")
        return
    
    # Chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display chat history
    for message in st.session_state.chat_history[-10:]:
        if message['role'] == 'user':
            st.markdown(
                f'<div class="chat-message chat-user"><b>You:</b> {message["content"]}</div>', 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="chat-message chat-assistant"><b>Assistant:</b> {message["content"]}</div>', 
                unsafe_allow_html=True
            )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input at bottom of right sidebar
    user_question = st.text_input(
        "Ask a question about the course...",
        key="chat_input",
        placeholder="Type your question here..."
    )
    
    if user_question and st.session_state.get('groq_client'):
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_question,
            'timestamp': datetime.now().isoformat()
        })
        
        # Generate AI response
        with st.spinner("Thinking..."):
            try:
                course = st.session_state.current_course
                current_slide = course['slides'][st.session_state.current_slide]
                
                prompt = f"""
                Course: {course['original_pdf_name']}
                Current Section: {current_slide.get('section_title', 'General')}
                Current Slide: {current_slide['title']}
                Slide Content: {current_slide['content'][:500]}
                
                User Question: {user_question}
                
                Provide a helpful, accurate answer based on the course content.
                """
                
                response = st.session_state.groq_client.make_request(
                    prompt,
                    system_message="You are a helpful course assistant. Answer questions based on the course content.",
                    temperature=0.7
                )
                
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': response,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Clear the input
                st.session_state.chat_input = ""
                st.rerun()
                
            except Exception as e:
                st.error(f"Failed to get response: {str(e)}")

def evaluate_answer(slide_idx):
    """Evaluate quiz answer"""
    if slide_idx not in st.session_state.user_answers:
        st.warning("Please provide an answer first")
        return
    
    slide = st.session_state.current_course['slides'][slide_idx]
    quiz = slide.get('quiz', {})
    
    if not quiz:
        st.error("No quiz data available")
        return
    
    user_answer = st.session_state.user_answers[slide_idx]
    
    with st.spinner("Evaluating your answer..."):
        evaluator = QuizEvaluator(st.session_state.groq_client)
        result = evaluator.evaluate_answer(user_answer, quiz, slide['title'])
        
        st.session_state[f"quiz_result_{slide_idx}"] = result
        save_progress()
        show_quiz_result(slide_idx)

def show_quiz_result(slide_idx):
    """Display quiz evaluation result"""
    result = st.session_state.get(f"quiz_result_{slide_idx}")
    if not result:
        return
    
    if result.get('is_correct', False):
        st.success("✅ Correct! Well done!")
    else:
        st.error("❌ Not quite right. Keep learning!")
    
    if 'score' in result:
        st.info(f"**Score:** {result['score']}/10")
    
    if result.get('feedback'):
        st.write(f"**Feedback:** {result['feedback']}")

def add_bookmark(slide_idx):
    """Add current slide to bookmarks"""
    if slide_idx not in st.session_state.bookmarks:
        st.session_state.bookmarks.append(slide_idx)
        st.session_state.bookmarks.sort()
        save_progress()

def save_progress():
    """Save user progress to storage"""
    if st.session_state.current_course:
        progress = {
            "current_slide": st.session_state.current_slide,
            "quiz_answers": st.session_state.user_answers,
            "bookmarks": st.session_state.bookmarks,
            "last_accessed": datetime.now().isoformat()
        }
        
        st.session_state.storage_manager.save_user_progress(
            st.session_state.current_course['course_id'],
            st.session_state.user_id,
            progress
        )

def show_progress_page():
    """Show user progress and statistics"""
    st.subheader("📊 My Learning Progress")
    
    user_courses = st.session_state.storage_manager.list_user_courses(st.session_state.user_id)
    
    if not user_courses:
        st.info("No course progress found. Create or load a course to get started!")
        return
    
    for course_info in user_courses:
        course_data = course_info['course_data']
        progress = course_info['progress']
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**{course_data['original_pdf_name']}**")
            st.write(f"Created: {course_data['created_date'][:10]}")
            
            completion = len(progress.get('quiz_answers', {})) / max(len(course_data.get('slides', [])), 1)
            st.progress(completion)
            st.write(f"Completion: {int(completion * 100)}%")
        
        with col2:
            st.write(f"📚 {len(course_data['slides'])} slides")
            st.write(f"✅ {len(progress.get('quiz_answers', {}))} quizzes done")
        
        with col3:
            if st.button("📖 Study", key=f"study_{course_info['course_id']}"):
                load_existing_course(course_info['course_id'])

def main():
    """Main application function"""
    apply_custom_css()
    initialize_session_state()
    show_sidebar()
    
    if st.session_state.current_view == "home":
        show_home_page()
    elif st.session_state.current_view == "study":
        show_study_interface()
    elif st.session_state.current_view == "progress":
        show_progress_page()

if __name__ == "__main__":
    main()
