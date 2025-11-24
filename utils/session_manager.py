import uuid
from datetime import datetime

class SessionManager:
    """
    Manages chat sessions and conversation history.
    Now stores data in Flask session for persistence across requests.
    """
    
    def __init__(self):
        # In-memory fallback for sessions (mainly for session metadata)
        self.sessions = {}
    
    def create_session(self):
        """Create a new chat session."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'id': session_id,
            'created_at': datetime.now().isoformat(),
            'messages': []
        }
        return session_id
    
    def get_session(self, session_id):
        """Get session data."""
        return self.sessions.get(session_id, {'messages': []})
    
    def add_message(self, session_id, role, content, sources=None):
        """Add a message to session history."""
        if session_id not in self.sessions:
            # Create session if it doesn't exist
            self.sessions[session_id] = {
                'id': session_id,
                'created_at': datetime.now().isoformat(),
                'messages': []
            }
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        if sources:
            message['sources'] = sources
        
        self.sessions[session_id]['messages'].append(message)
        
        print(f"   💾 Message added. Total messages in session: {len(self.sessions[session_id]['messages'])}")
        
        return True
    
    def get_conversation_history(self, session_id):
        """Get conversation history for a session."""
        if session_id not in self.sessions:
            print(f"   ⚠️  Session {session_id[:8]} not found in memory")
            return []
        
        messages = self.sessions[session_id].get('messages', [])
        print(f"   💬 Retrieved {len(messages)} messages from session {session_id[:8]}")
        return messages
    
    def clear_session(self, session_id):
        """Clear a session (for new chat)."""
        if session_id in self.sessions:
            self.sessions[session_id]['messages'] = []
            return True
        return False
    
    def delete_session(self, session_id):
        """Delete a session completely."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
