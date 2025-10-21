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
    with open('assets/default_style.css') as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'current_course': None,
        'current_slide': 0,
        'user_answers': {},
        'bookmarks': [],
        'chat_history': [],
        'current_view': 'home',
        'user_id': str(hash(str(time.time())))[:8],  # Simple session-based ID
        'groq_client': None,
        'storage_manager': StorageManager(),
        'processed_courses': [],
        'last_course_loaded': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def show_sidebar():
    """Sidebar navigation and course info"""
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
            
            if google_api_key and cse_id:
                st.session_state.google_api_key = google_api_key
                st.session_state.cse_id = cse_id
                try:
                    image_search = ImageSearch(google_api_key, cse_id)
                    if image_search.validate_credentials():
                        st.success("✅ Google API connected")
                    else:
                        st.error("❌ Google API validation failed")
                except Exception as e:
                    st.warning(f"⚠️ Image search may not work: {str(e)}")
        
        st.markdown("---")
        
        # Navigation
        st.subheader("📚 Navigation")
        
        nav_options = {
            "🏠 Create/Load Course": "home",
            "📖 Study": "study", 
            "💬 Ask Questions": "chat",
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
            st.write(f"🎯 {course['processing_metadata']['difficulty_level']}")
            
            # Progress
            progress = len(st.session_state.user_answers) / len(course['slides'])
            st.progress(progress)
            st.write(f"Progress: {int(progress * 100)}%")
            
            # Quick actions
            st.markdown("---")
            st.subheader("⚡ Quick Actions")
            
            if st.button("🔄 Reset Progress", use_container_width=True):
                st.session_state.user_answers = {}
                st.session_state.bookmarks = []
                st.session_state.current_slide = 0
                st.success("Progress reset!")
                st.rerun()
            
            if st.button("📤 Export Course", use_container_width=True):
                export_course()

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
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        enable_images = st.checkbox("Enable Image Search", value=True, 
                                  help="Search and add relevant images (requires Google API)")
        estimated_time = "2-5 minutes"  # Default estimation
    
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
    
    # Option 1: Upload JSON file
    uploaded_json = st.file_uploader(
        "Upload Course File", 
        type=['json'],
        help="Upload a previously generated .json course file"
    )
    
    if uploaded_json and st.button("📖 Load Uploaded Course", use_container_width=True):
        load_course_from_file(uploaded_json)
    
    st.markdown("---")
    
    # Option 2: Load from local storage
    st.subheader("📚 My Recent Courses")
    
    user_courses = st.session_state.storage_manager.list_user_courses(st.session_state.user_id)
    
    if not user_courses:
        st.info("No recent courses found. Create your first course!")
    else:
        for course_info in user_courses[:5]:  # Show last 5 courses
            course_data = course_info['course_data']
            progress = course_info['progress']
            
            completion = len(progress.get('quiz_answers', {})) / len(course_data.get('slides', [1]))
            
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
    results_placeholder = st.empty()
    
    try:
        # Initialize components
        pdf_processor = PDFProcessor()
        groq_client = GroqClient(st.session_state.groq_api_key)
        
        # Step 1: Process PDF
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
        
        # Step 2: Generate TOC
        status_text.text("📑 Creating table of contents...")
        toc = groq_client.generate_toc(pdf_text, user_prompt)
        progress_bar.progress(30)
        
        # Step 3: Initialize image search if enabled
        image_search = None
        if enable_images and st.session_state.get('google_api_key') and st.session_state.get('cse_id'):
            image_search = ImageSearch(st.session_state.google_api_key, st.session_state.cse_id)
            status_text.text("🖼️ Image search enabled...")
        else:
            status_text.text("⏭️ Image search disabled...")
        
        # Step 4: Generate content
        status_text.text("🎨 Creating study slides...")
        content_generator = ContentGenerator(groq_client)
        
        # Estimate processing time
        estimated_time = content_generator.estimate_processing_time(toc)
        results_placeholder.info(f"⏱️ Estimated processing time: {estimated_time}")
        
        all_slides = content_generator.generate_course_content(
            toc, pdf_text, user_prompt, course_id, image_search
        )
        progress_bar.progress(80)
        
        # Step 5: Save course
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
                "completion_time": estimated_time,
                "difficulty_level": detect_difficulty_level(user_prompt),
                "has_images": any(slide.get('image_path') for slide in all_slides)
            }
        }
        
        st.session_state.storage_manager.save_course(course_id, course_data)
        
        # Load into session
        st.session_state.current_course = course_data
        st.session_state.current_view = "study"
        st.session_state.current_slide = 0
        st.session_state.user_answers = {}
        st.session_state.bookmarks = []
        
        progress_bar.progress(100)
        status_text.text("✅ Course ready! Redirecting...")
        
        # Show completion summary
        with results_placeholder.container():
            st.success("🎉 Course created successfully!")
            st.write(f"**Summary:**")
            st.write(f"- 📑 {len(toc)} sections")
            st.write(f"- 📚 {len(all_slides)} slides")
            st.write(f"- ❓ {sum(1 for slide in all_slides if slide.get('quiz'))} quizzes")
            if course_data['processing_metadata']['has_images']:
                st.write(f"- 🖼️ Includes educational images")
        
        time.sleep(2)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error creating course: {str(e)}")
        status_text.text("💥 Failed to create course")
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
        
        # Validate course structure
        required_fields = ['course_id', 'slides', 'toc']
        if all(field in course_data for field in required_fields):
            st.session_state.current_course = course_data
            st.session_state.current_slide = 0
            st.session_state.current_view = "study"
            
            # Load or initialize user progress
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
        
        # Load user progress
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
    """Main study interface"""
    if not st.session_state.current_course:
        st.warning("📚 Please load a course first")
        st.session_state.current_view = "home"
        st.rerun()
        return
    
    course = st.session_state.current_course
    current_slide_idx = st.session_state.current_slide
    current_slide = course['slides'][current_slide_idx]
    
    # Main layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        display_slide_content(current_slide_idx)
        show_navigation_controls(current_slide_idx)
    
    with col2:
        show_sidebar_content(current_slide_idx)

def display_slide_content(slide_idx):
    """Display slide content with enhanced formatting"""
    slide = st.session_state.current_course['slides'][slide_idx]
    
    st.markdown(f'<div class="slide-card">', unsafe_allow_html=True)
    
    # Slide header with section info
    st.markdown(f"### {slide['title']}")
    if slide.get('section_title'):
        st.caption(f"Section: {slide['section_title']}")
    
    # Slide content
    st.markdown(slide['content'])
    
    # Key points
    if slide.get('key_points'):
        st.markdown("**Key Points:**")
        for point in slide['key_points']:
            st.markdown(f"- {point}")
    
    # Image
    if slide.get('image_path') and os.path.exists(slide['image_path']):
        st.image(slide['image_path'], use_column_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_navigation_controls(current_slide_idx):
    """Show navigation and interaction controls"""
    course = st.session_state.current_course
    total_slides = len(course['slides'])
    
    # Navigation buttons
    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
    
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
        current_slide = course['slides'][current_slide_idx]
        if 'quiz' in current_slide:
            if st.button("✅ Check Answer", type="primary", use_container_width=True):
                evaluate_answer(current_slide_idx)
        else:
            if st.button("🔖 Bookmark", use_container_width=True):
                add_bookmark(current_slide_idx)
                st.success("📌 Slide bookmarked!")
    
    with col4:
        # Progress indicator
        st.write(f"**{current_slide_idx + 1} / {total_slides}**")
    
    # Progress bar
    progress = (current_slide_idx + 1) / total_slides
    st.progress(progress)

def show_sidebar_content(current_slide_idx):
    """Show sidebar content (TOC, quizzes, bookmarks)"""
    course = st.session_state.current_course
    
    # Table of Contents
    with st.expander("📑 Table of Contents", expanded=True):
        for i, section in enumerate(course['toc']):
            is_current = current_slide_idx >= section.get('start_slide', 0) and \
                        current_slide_idx < section.get('start_slide', 0) + section.get('estimated_slides', 3)
            
            emoji = "📍" if is_current else "📖"
            if st.button(f"{emoji} {section['title']}", 
                        key=f"toc_{i}",
                        use_container_width=True):
                st.session_state.current_slide = section.get('start_slide', 0)
                save_progress()
                st.rerun()
    
    # Quiz section
    current_slide = course['slides'][current_slide_idx]
    if 'quiz' in current_slide:
        show_quiz_interface(current_slide_idx)
    
    # Bookmarks
    if st.session_state.bookmarks:
        with st.expander("🔖 Bookmarks", expanded=True):
            for bookmark_idx in st.session_state.bookmarks:
                if bookmark_idx < len(course['slides']):
                    slide_title = course['slides'][bookmark_idx]['title']
                    if st.button(f"📍 {slide_title[:25]}...", 
                                key=f"bm_{bookmark_idx}",
                                use_container_width=True):
                        st.session_state.current_slide = bookmark_idx
                        save_progress()
                        st.rerun()

def show_quiz_interface(slide_idx):
    """Display and handle quiz interface"""
    slide = st.session_state.current_course['slides'][slide_idx]
    quiz = slide['quiz']
    
    st.markdown('<div class="quiz-box">', unsafe_allow_html=True)
    st.subheader("❓ Quick Check")
    st.write(quiz['question'])
    
    user_answer_key = f"quiz_{slide_idx}"
    
    if quiz['type'] == 'multiple_choice':
        options = quiz['options']
        user_answer = st.radio("Select your answer:", 
                              options, 
                              key=user_answer_key,
                              index=None)
        st.session_state.user_answers[slide_idx] = user_answer
        
    elif quiz['type'] == 'multi_select':
        options = quiz['options']
        user_answer = st.multiselect("Select all that apply:", 
                                    options, 
                                    key=user_answer_key)
        st.session_state.user_answers[slide_idx] = user_answer
        
    elif quiz['type'] == 'short_answer':
        user_answer = st.text_area("Your answer:", 
                                  key=user_answer_key, 
                                  height=100,
                                  placeholder="Type your answer here...")
        st.session_state.user_answers[slide_idx] = user_answer
    
    # Show previous evaluation if exists
    if f"quiz_result_{slide_idx}" in st.session_state:
        show_quiz_result(slide_idx)
    
    st.markdown('</div>', unsafe_allow_html=True)

def evaluate_answer(slide_idx):
    """Evaluate quiz answer"""
    if slide_idx not in st.session_state.user_answers:
        st.warning("Please provide an answer first")
        return
    
    slide = st.session_state.current_course['slides'][slide_idx]
    quiz = slide['quiz']
    user_answer = st.session_state.user_answers[slide_idx]
    
    with st.spinner("🤔 Evaluating your answer..."):
        evaluator = QuizEvaluator(st.session_state.groq_client)
        result = evaluator.evaluate_answer(user_answer, quiz, slide['title'])
        
        # Store result in session state
        st.session_state[f"quiz_result_{slide_idx}"] = result
        
        # Update progress
        st.session_state.user_answers[slide_idx] = user_answer
        save_progress()
        
        # Show result
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
    
    if result.get('correct_answer'):
        st.write(f"**Correct answer:** {result['correct_answer']}")

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

def show_chat_interface():
    """Chat interface for asking questions about the course"""
    st.subheader("💬 Course Assistant")
    
    if not st.session_state.current_course:
        st.info("Please load a course first to ask questions")
        return
    
    # Display chat history
    for message in st.session_state.chat_history[-10:]:  # Show last 10 messages
        if message['role'] == 'user':
            st.markdown(f'<div class="chat-message chat-user"><b>You:</b> {message["content"]}</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message chat-assistant"><b>Assistant:</b> {message["content"]}</div>', 
                       unsafe_allow_html=True)
    
    # Chat input
    user_question = st.chat_input("Ask a question about the course content...")
    
    if user_question and st.session_state.get('groq_client'):
        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_question,
            'timestamp': datetime.now().isoformat()
        })
        
        # Generate AI response
        with st.spinner("🤔 Thinking..."):
            try:
                # Get current course context
                course = st.session_state.current_course
                current_slide = course['slides'][st.session_state.current_slide]
                
                prompt = f"""
                Course: {course['original_pdf_name']}
                Current Section: {current_slide.get('section_title', 'General')}
                Current Slide: {current_slide['title']}
                Slide Content: {current_slide['content'][:500]}
                
                User Question: {user_question}
                
                Provide a helpful, accurate answer based on the course content.
                If you're unsure, suggest reviewing specific slides or sections.
                """
                
                response = st.session_state.groq_client.make_request(
                    prompt,
                    system_message="You are a helpful course assistant. Answer questions based on the course content.",
                    temperature=0.7
                )
                
                # Add assistant response to history
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': response,
                    'timestamp': datetime.now().isoformat()
                })
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Failed to get response: {str(e)}")

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
            
            # Progress bar
            completion = len(progress.get('quiz_answers', {})) / len(course_data.get('slides', [1]))
            st.progress(completion)
            st.write(f"Completion: {int(completion * 100)}%")
        
        with col2:
            st.write(f"📚 {len(course_data['slides'])} slides")
            st.write(f"✅ {len(progress.get('quiz_answers', {}))} quizzes done")
        
        with col3:
            if st.button("📖 Study", key=f"study_{course_info['course_id']}"):
                load_existing_course(course_info['course_id'])
            
            if st.button("📤 Export", key=f"export_{course_info['course_id']}"):
                export_course(course_info['course_id'])

def export_course(course_id=None):
    """Export course to downloadable JSON file"""
    if not course_id and st.session_state.current_course:
        course_id = st.session_state.current_course['course_id']
    
    if course_id:
        course_data = st.session_state.storage_manager.load_course(course_id)
        if course_data:
            # Create downloadable JSON
            import json
            json_str = json.dumps(course_data, indent=2)
            
            st.download_button(
                label="📥 Download Course File",
                data=json_str,
                file_name=f"{course_data['original_pdf_name']}_{course_id[:8]}.json",
                mime="application/json"
            )
        else:
            st.error("Course not found for export")
    else:
        st.warning("No course loaded to export")

def main():
    """Main application function"""
    # Apply styling and initialization
    apply_custom_css()
    initialize_session_state()
    
    # Show sidebar
    show_sidebar()
    
    # Main content area based on current view
    if st.session_state.current_view == "home":
        show_home_page()
    elif st.session_state.current_view == "study":
        show_study_interface()
    elif st.session_state.current_view == "chat":
        show_chat_interface()
    elif st.session_state.current_view == "progress":
        show_progress_page()
    
    # Auto-save progress when leaving study view
    if hasattr(st, '_session_state') and st.session_state.current_view != "study":
        save_progress()

if __name__ == "__main__":
    main()
