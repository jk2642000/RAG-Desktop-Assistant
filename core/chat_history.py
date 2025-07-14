import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

class ChatHistoryManager:
    def __init__(self, db_path: str = "data/chat_history.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize chat history database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT,
                created_at DATETIME,
                updated_at DATETIME
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                message_type TEXT,
                content TEXT,
                sources TEXT,
                rating INTEGER,
                timestamp DATETIME,
                FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_session(self, title: str = None) -> str:
        """Create new chat session"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not title:
            title = f"Chat {session_id}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_sessions (session_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (session_id, title, datetime.now(), datetime.now()))
        
        conn.commit()
        conn.close()
        return session_id
    
    def save_message(self, session_id: str, message_type: str, content: str, 
                    sources: List[str] = None, rating: int = None):
        """Save message to chat history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sources_json = json.dumps(sources) if sources else None
        
        cursor.execute('''
            INSERT INTO chat_messages (session_id, message_type, content, sources, rating, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, message_type, content, sources_json, rating, datetime.now()))
        
        # Update session timestamp
        cursor.execute('''
            UPDATE chat_sessions SET updated_at = ? WHERE session_id = ?
        ''', (datetime.now(), session_id))
        
        conn.commit()
        conn.close()
    
    def get_sessions(self) -> List[Dict]:
        """Get all chat sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT session_id, title, created_at, updated_at
            FROM chat_sessions
            ORDER BY updated_at DESC
        ''')
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'session_id': row[0],
                'title': row[1],
                'created_at': row[2],
                'updated_at': row[3]
            })
        
        conn.close()
        return sessions
    
    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Get messages for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message_type, content, sources, rating, timestamp
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
        ''', (session_id,))
        
        messages = []
        for row in cursor.fetchall():
            sources = json.loads(row[2]) if row[2] else []
            messages.append({
                'type': row[0],
                'content': row[1],
                'sources': sources,
                'rating': row[3],
                'timestamp': row[4]
            })
        
        conn.close()
        return messages
    
    def delete_session(self, session_id: str):
        """Delete a chat session and its messages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM chat_messages WHERE session_id = ?', (session_id,))
        cursor.execute('DELETE FROM chat_sessions WHERE session_id = ?', (session_id,))
        
        conn.commit()
        conn.close()
    
    def update_session_title(self, session_id: str, title: str):
        """Update session title"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE chat_sessions SET title = ?, updated_at = ? WHERE session_id = ?
        ''', (title, datetime.now(), session_id))
        
        conn.commit()
        conn.close()

# Global instance
chat_history = ChatHistoryManager()