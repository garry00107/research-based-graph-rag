from typing import List, Dict, Optional
from datetime import datetime
import json
from cache import cache

import uuid

class Message:
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None, id: str = None):
        self.id = id or str(uuid.uuid4())
        self.role = role  # 'user' or 'assistant'
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            id=data.get('id')
        )

class ChatHistoryManager:
    def __init__(self):
        self.cache = cache
        self.max_history = 10  # Keep last 10 messages for context
    
    def _get_conversation_key(self, conversation_id: str) -> str:
        return f"conv:{conversation_id}"
    
    def add_message(self, conversation_id: str, role: str, content: str):
        """Add a message to conversation history"""
        key = self._get_conversation_key(conversation_id)
        
        # Get existing history
        history = self.get_history(conversation_id)
        
        # Add new message
        message = Message(role, content)
        history.append(message.to_dict())
        
        # Keep only last N messages
        if len(history) > self.max_history:
            history = history[-self.max_history:]
        
        # Save to cache (24 hour TTL)
        if self.cache.enabled:
            try:
                self.cache.client.setex(
                    key,
                    86400,  # 24 hours
                    json.dumps(history)
                )
            except Exception as e:
                print(f"Error saving chat history: {e}")
    
    def get_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history"""
        if not self.cache.enabled:
            return []
        
        try:
            key = self._get_conversation_key(conversation_id)
            cached = self.cache.client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            print(f"Error loading chat history: {e}")
        
        return []
    
    def get_context_string(self, conversation_id: str) -> str:
        """Get conversation history as a formatted string for LLM context"""
        history = self.get_history(conversation_id)
        if not history:
            return ""
        
        context_parts = []
        for msg in history:
            role = msg['role'].capitalize()
            content = msg['content']
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    def add_feedback(self, conversation_id: str, message_id: str, feedback: str) -> bool:
        """Add feedback (up/down) to a specific message"""
        if not self.cache.enabled:
            return False
        
        try:
            key = self._get_conversation_key(conversation_id)
            history = self.get_history(conversation_id)
            
            updated_history = []
            found = False
            for msg in history:
                if msg.get("id") == message_id:
                    msg["feedback"] = feedback
                    found = True
                updated_history.append(msg)
            
            if found:
                # Save updated history
                self.cache.client.setex(
                    key,
                    86400,  # 24 hours
                    json.dumps(updated_history)
                )
                return True
            else:
                return False # Message not found
        except Exception as e:
            print(f"Error adding feedback to chat history: {e}")
            return False
        
    def clear_history(self, conversation_id: str):
        """Clear conversation history"""
        if not self.cache.enabled:
            return
        
        try:
            key = self._get_conversation_key(conversation_id)
            self.cache.client.delete(key)
        except Exception as e:
            print(f"Error clearing chat history: {e}")

# Global instance
chat_history = ChatHistoryManager()
