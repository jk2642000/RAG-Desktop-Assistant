# 🤖 RAG Desktop Assistant

> **A powerful, portable document Q&A system powered by Google Gemini AI with advanced analytics and ML insights.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![RAG](https://img.shields.io/badge/RAG-Enabled-green.svg)](https://github.com/)

## 🌟 What is RAG Desktop Assistant?

RAG Desktop Assistant is an intelligent document analysis tool that lets you upload various document formats and ask questions about their content using advanced AI. Built with Google Gemini AI and featuring comprehensive analytics, it's perfect for researchers, students, professionals, and anyone who needs to quickly extract insights from documents.

## 🚀 Quick Start

### Option 1: One-Click Launch (Windows)
- **RAG_Desktop_Assistant.bat** (Windows Batch)
- **RAG_Desktop_Assistant.ps1** (PowerShell)

### Option 2: Manual Start
```bash
python main.py
```

## 📋 Requirements

- **Python 3.8+** ([Download from python.org](https://www.python.org/downloads/))
- **Google Gemini API Key** ([Get free key](https://makersuite.google.com/app/apikey))
- **Internet connection** (for AI processing and first-time setup)
- **~2GB disk space** (for AI models and dependencies)

## 🚀 Quick Demo

Try with our example documents:
```bash
# 1. Upload examples/company_report.txt
# 2. Ask: "What was the revenue growth percentage?"
# 3. Get: "23% growth from $102.1M to $125.7M" + source citation
```

## 🔧 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/rag-desktop-assistant.git
cd rag-desktop-assistant
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Key
1. Copy `.env.example` to `.env`
2. Add your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

### 4. Run the Application
```bash
python main.py
```

## 🏗️ Architecture

```
rag-desktop-assistant/
├── main.py                 # Application entry point
├── core/                   # Core RAG system
│   ├── rag_engine.py      # Main RAG orchestrator
│   ├── document_processor.py # Multi-format document parsing
│   ├── vector_store.py    # ChromaDB integration
│   ├── gemini_processor.py # Google Gemini AI integration
│   ├── analytics.py       # Performance tracking
│   ├── ml_analytics.py    # ML-powered insights
│   └── chat_history.py    # Conversation persistence
├── ui/                     # PyQt5 user interface
│   ├── main_window.py     # Main application window
│   ├── chat_widget.py     # Chat interface
│   └── document_panel.py  # Document management
├── analytics_dashboard.py # Standalone analytics dashboard
└── requirements.txt       # Python dependencies
```

## 🎯 Usage

1. **Upload documents** (PDF, TXT, DOCX, XLSX, CSV, PPTX)
2. **Ask questions** about your documents
3. **Rate responses** to improve AI
4. **Save chat history** automatically
5. **Export conversations** to TXT/PDF
6. **View analytics** with analytics dashboard

## 🌟 Why Choose RAG Desktop Assistant?

**Unlike ChatGPT or Gemini**, RAG Desktop Assistant:
- 📁 **Analyzes YOUR documents** - Upload PDFs, Excel files, presentations
- 🔒 **Runs locally** - Your data stays private on your machine
- 📚 **Provides source citations** - Know exactly where answers come from
- 💾 **Remembers everything** - Persistent chat history and document memory
- 🧮 **Built-in tools** - Calculator, date operations, text analysis
- 📊 **Advanced analytics** - ML-powered insights and performance tracking

**See [SHOWCASE.md](SHOWCASE.md) for detailed examples and comparisons!**

## 🔑 API Key Setup

1. Copy `.env.example` to `.env`
2. Add your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## 🆘 Troubleshooting

- **Python not found**: Install from python.org
- **Dependencies fail**: Run as administrator
- **App won't start**: Check .env file has API key
- **Slow responses**: Check internet connection

## ✨ Features

### 📄 **Document Support**
- **PDF, TXT, DOCX** - Standard document formats
- **XLSX, XLS, CSV** - Spreadsheet and data files
- **PPTX** - PowerPoint presentations
- **Drag & Drop** - Easy file upload

### 💬 **Chat Features**
- **Auto-save conversations** - Never lose your chats
- **Chat history browser** - Access previous conversations
- **Export to TXT/PDF** - Share conversations professionally
- **Session management** - Organize your chats

### 🤖 **AI Capabilities**
- **Google Gemini AI** - Advanced language model
- **Function calling** - Calculator, date operations, text analysis
- **Streaming responses** - Real-time AI responses
- **Source citations** - Know where answers come from

### 📊 **Analytics Dashboard**

Run analytics dashboard:
```bash
python analytics_dashboard.py
```
- **Performance metrics** - Response times, success rates
- **ML-powered insights** - Question patterns, optimization tips
- **User satisfaction tracking** - Rating analysis
- **Export reports** - Detailed analytics export

## 🎮 **How to Use**

### **Basic Workflow:**
1. **Start the app** - Double-click launcher or run `python main.py`
2. **Upload documents** - Drag files or click "Upload Documents"
3. **Ask questions** - Type questions about your documents
4. **Rate responses** - Help improve AI with feedback
5. **Export chats** - Save conversations for later

### **Keyboard Shortcuts:**
- **Ctrl+N** - Start new chat session
- **Enter** - Send message
- **Ctrl+Enter** - Send message (alternative)

### **File Management:**
- **Delete documents** - Right-click → Delete
- **Re-index files** - Automatically detects file changes
- **Multiple formats** - Mix different document types

## 🧪 Testing

Run tests to verify functionality:
```bash
# Run all tests
python -m pytest tests/ -v

# Or run individual tests
python tests/test_chat_exporter.py
python tests/test_vector_store.py

# Run system integration tests
python system_tests.py
```

## 🛣️ Roadmap

See our [ROADMAP.md](ROADMAP.md) for planned features and development timeline.

## 🤝 Contributing

This project is actively maintained by:
- **[Your Name]** - [@your-github-username](https://github.com/your-github-username)
- **[Collaborator Name]** - [@collaborator-username](https://github.com/collaborator-username)

We welcome contributions! Please feel free to submit issues, feature requests, or pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini AI for powerful language processing
- ChromaDB for efficient vector storage
- PyQt5 for the desktop interface
- All the amazing open-source libraries that make this possible

---

**Your RAG Desktop Assistant is ready to transform how you work with documents! 🎉**
