import os
from datetime import datetime
from typing import List, Dict
from .chat_history import chat_history

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

class ChatExporter:
    def __init__(self):
        self.styles = None
        if PDF_AVAILABLE:
            self._init_pdf_styles()
    
    def _init_pdf_styles(self):
        """Initialize PDF styles"""
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name='UserMessage',
            parent=self.styles['Normal'],
            leftIndent=20,
            textColor='blue'
        ))
        self.styles.add(ParagraphStyle(
            name='AssistantMessage',
            parent=self.styles['Normal'],
            leftIndent=20,
            textColor='green'
        ))
    
    def export_to_txt(self, session_id: str, file_path: str) -> bool:
        """Export chat session to TXT file"""
        try:
            messages = chat_history.get_session_messages(session_id)
            sessions = chat_history.get_sessions()
            
            # Find session title
            session_title = "Chat Session"
            for session in sessions:
                if session['session_id'] == session_id:
                    session_title = session['title']
                    break
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"RAG Desktop Assistant - Chat Export\n")
                f.write(f"Session: {session_title}\n")
                f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                
                for msg in messages:
                    timestamp = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M:%S')
                    
                    if msg['type'] == 'user':
                        f.write(f"[{timestamp}] You: {msg['content']}\n\n")
                    elif msg['type'] == 'assistant':
                        f.write(f"[{timestamp}] Assistant: {msg['content']}\n")
                        if msg['sources']:
                            f.write(f"Sources: {', '.join(msg['sources'])}\n")
                        if msg['rating']:
                            f.write(f"Rating: {msg['rating']}/5\n")
                        f.write("\n")
                    elif msg['type'] == 'system':
                        f.write(f"[{timestamp}] System: {msg['content']}\n\n")
            
            return True
        except Exception as e:
            print(f"Error exporting to TXT: {e}")
            return False
    
    def export_to_pdf(self, session_id: str, file_path: str) -> bool:
        """Export chat session to PDF file"""
        if not PDF_AVAILABLE:
            return False
        
        try:
            messages = chat_history.get_session_messages(session_id)
            sessions = chat_history.get_sessions()
            
            # Find session title
            session_title = "Chat Session"
            for session in sessions:
                if session['session_id'] == session_id:
                    session_title = session['title']
                    break
            
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            story = []
            
            # Header
            story.append(Paragraph("RAG Desktop Assistant - Chat Export", self.styles['Title']))
            story.append(Paragraph(f"Session: {session_title}", self.styles['Heading2']))
            story.append(Paragraph(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Messages
            for msg in messages:
                timestamp = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M:%S')
                
                if msg['type'] == 'user':
                    story.append(Paragraph(f"<b>[{timestamp}] You:</b> {msg['content']}", self.styles['UserMessage']))
                elif msg['type'] == 'assistant':
                    story.append(Paragraph(f"<b>[{timestamp}] Assistant:</b> {msg['content']}", self.styles['AssistantMessage']))
                    if msg['sources']:
                        story.append(Paragraph(f"<i>Sources: {', '.join(msg['sources'])}</i>", self.styles['Normal']))
                    if msg['rating']:
                        story.append(Paragraph(f"<i>Rating: {msg['rating']}/5</i>", self.styles['Normal']))
                elif msg['type'] == 'system':
                    story.append(Paragraph(f"<b>[{timestamp}] System:</b> {msg['content']}", self.styles['Normal']))
                
                story.append(Spacer(1, 0.1*inch))
            
            doc.build(story)
            return True
        except Exception as e:
            print(f"Error exporting to PDF: {e}")
            return False
    
    def export_session(self, session_id: str, file_path: str, format_type: str = 'txt') -> bool:
        """Export session in specified format"""
        if format_type.lower() == 'pdf' and PDF_AVAILABLE:
            return self.export_to_pdf(session_id, file_path)
        else:
            return self.export_to_txt(session_id, file_path)

# Global instance
chat_exporter = ChatExporter()