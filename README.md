# AI PDF Study Guide

## Overview
AI PDF Study Guide is an intelligent learning companion that transforms your PDF documents into interactive study materials. Upload any PDF and get instant access to AI-powered features including content summaries, interactive quizzes, educational diagrams, and a smart chatbot tutor.

## Features

### 📚 Smart Content Generation
- **Automatic Slide Creation**: Converts PDF content into educational slides with descriptive content
- **Visual Learning**: Integrates relevant images, diagrams, and flowcharts from multiple sources
- **Educational Diagrams**: Auto-generates flowcharts, mind maps, and visual aids using Mermaid and Matplotlib

### 💬 Interactive Chat
- **AI Tutor**: Ask questions about your PDF content and get instant, intelligent responses
- **Context-Aware**: The AI understands your document and provides relevant explanations
- **Seamless Interface**: Chat updates automatically without needing to click "Next"

### 📝 Quiz Generation
- **Separate Quiz Section**: Dedicated slide for interactive quizzes
- **Smart Questions**: AI generates questions based on your PDF content
- **Instant Feedback**: Get immediate evaluation and explanations

### 🖼️ Rich Media Integration
- **Image Search**: Automatically finds relevant educational images
- **AI-Generated Visuals**: Uses Groq API to create custom diagrams
- **Flowcharts & Diagrams**: Mermaid and Matplotlib integration for educational visualizations

### 🤖 Multi-Agent Architecture
- **Distributed Processing**: Multiple specialized AI agents work together
- **Reduced Load**: Efficient task distribution prevents single-agent overload
- **Better Performance**: Faster responses and higher quality outputs

## 🚀 Try It Now - FREE!

**[Launch the App](https://ai-pdf-study-guide.streamlit.app/)**

No installation required! Just visit the link above and start learning.

## Local Installation

If you prefer to run the app locally:

```bash
# Clone the repository
git clone https://github.com/Advait369/streamlit-study-website.git
cd streamlit-study-website

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

## Requirements

- Python 3.8+
- Streamlit
- PyPDF2 or pdfplumber
- Groq API
- Additional dependencies listed in `requirements.txt`

## Project Structure

```
streamlit-study-website/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── utils/                 # Utility modules
│   ├── content_generator.py   # Content generation logic
│   ├── groq_client.py         # Groq API integration
│   ├── image_search.py        # Image search functionality
│   ├── pdf_processor.py       # PDF processing
│   ├── quiz_evaluator.py      # Quiz generation and evaluation
│   └── __init__.py
├── assets/                # Static assets
└── .streamlit/            # Streamlit configuration
```

## How It Works

1. **Upload**: Select any PDF document
2. **Process**: AI analyzes and extracts key information
3. **Generate**: Creates slides, quizzes, and visual aids
4. **Learn**: Interact with content through chat, quizzes, and slides
5. **Master**: Use diagrams and flowcharts to deepen understanding

## Key Improvements

✅ Instant AI responses in chat (no button clicking required)
✅ Responsive UI that fits any screen size
✅ Separate, organized sections for Chat, Content, and Data
✅ Scrollable chat interface that stays within its container
✅ No storage/backup complexity - streamlined experience
✅ Quiz as a dedicated separate section
✅ Descriptive content instead of keyword-based slides
✅ Verified, relevant images and diagrams
✅ AI-generated educational visuals
✅ Multi-agent system for optimal performance

## Technology Stack

- **Frontend**: Streamlit
- **AI/ML**: Groq API, Multi-agent architecture
- **Visualization**: Mermaid, Matplotlib, Plotly
- **PDF Processing**: PyPDF2/pdfplumber
- **Image Generation**: Groq API, Google Image Search

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Ready to transform your learning experience?**

## [🎯 Start Learning Now!](https://ai-pdf-study-guide.streamlit.app/)
