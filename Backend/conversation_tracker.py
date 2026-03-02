"""
Conversation History Tracker
For escalation pattern detection
"""

class ConversationTracker:
    def __init__(self):
        self.conversations = {}  # {user_id: [messages]}
    
    def init_user(self, user_id):
        """Initialize user conversation"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
    
    def add_message(self, user_id, message_text):
        """Add message to history"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].append(message_text)
        
        # Keep last 50 messages
        if len(self.conversations[user_id]) > 50:
            self.conversations[user_id] = self.conversations[user_id][-50:]
    
    def get_history(self, user_id, limit=10):
        """Get conversation history"""
        if user_id not in self.conversations:
            return []
        
        return self.conversations[user_id][-limit:]
    
    def clear_history(self, user_id):
        """Clear conversation (e.g., after blocking)"""
        if user_id in self.conversations:
            self.conversations[user_id] = []