"""
🛡️ SafeChat - Backend Safety System
Hackathon Project - Chat with Real-time Threat Detection
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import json

from safety_analyzer import SafetyAnalyzer
from conversation_tracker import ConversationTracker
from fake_account_detector import FakeAccountDetector

# ==================== FLASK SETUP ====================

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from frontend

# ==================== INITIALIZE SYSTEMS ====================

safety_analyzer = SafetyAnalyzer()
conversation_tracker = ConversationTracker()
fake_account_detector = FakeAccountDetector()

# ==================== IN-MEMORY DATABASE ====================

users_db = {}  # {user_id: user_data}
blocked_users = set()  # Blocked user IDs
messages_log = []  # All messages for analytics

# ==================== ROUTES ====================

# --- USER MANAGEMENT ---

@app.route('/api/users/create', methods=['POST'])
def create_user():
    """Create a new user for chat"""
    try:
        data = request.json
        user_id = data.get('user_id', f"user_{datetime.now().timestamp()}")
        username = data.get('username', 'Anonymous')
        
        users_db[user_id] = {
            'user_id': user_id,
            'username': username,
            'created_at': datetime.now(),
            'followers_count': data.get('followers_count', 0),
            'posts_count': data.get('posts_count', 0),
            'is_blocked': False,
            'messages_sent': 0,
            'warnings_received': 0
        }
        
        conversation_tracker.init_user(user_id)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'username': username,
            'message': f'User {username} created'
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user profile and stats"""
    if user_id not in users_db:
        return jsonify({'error': 'User not found'}), 404
    
    user = users_db[user_id]
    account_age = (datetime.now() - user['created_at']).days
    
    return jsonify({
        'user_id': user_id,
        'username': user['username'],
        'account_age_days': account_age,
        'followers_count': user['followers_count'],
        'posts_count': user['posts_count'],
        'is_blocked': user['is_blocked'],
        'messages_sent': user['messages_sent'],
        'warnings_received': user['warnings_received'],
        'created_at': user['created_at'].isoformat()
    }), 200


# --- CORE SAFETY ANALYSIS ---

@app.route('/api/analyze_message', methods=['POST'])
def analyze_message():
    """
    Main endpoint: Analyze incoming message for safety threats
    
    Request body:
    {
        'message': 'text content',
        'user_id': 'user123',
        'username': 'John'
    }
    
    Response:
    {
        'risk_score': 0-100+,
        'risk_level': 'Safe|Warning|Dangerous|Critical',
        'action': 'allow|warn|hide|block',
        'categories': ['Romance Scam', ...],
        'reasons': ['Found keyword X', ...],
        'should_escalate': true/false,
        'blocked': true/false
    }
    """
    try:
        data = request.json
        message_text = data.get('message', '').strip()
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', 'Unknown')
        
        # Validation
        if not message_text:
            return jsonify({'error': 'Empty message'}), 400
        
        if len(message_text) > 1000:
            return jsonify({'error': 'Message too long'}), 400
        
        # Check if already blocked
        if user_id in blocked_users:
            return jsonify({
                'risk_score': 100,
                'risk_level': 'Critical',
                'action': 'block',
                'reason': 'User is blocked',
                'blocked': True
            }), 200
        
        # Create user if doesn't exist
        if user_id not in users_db:
            users_db[user_id] = {
                'user_id': user_id,
                'username': username,
                'created_at': datetime.now(),
                'followers_count': 0,
                'posts_count': 0,
                'is_blocked': False,
                'messages_sent': 0,
                'warnings_received': 0
            }
            conversation_tracker.init_user(user_id)
        
        user = users_db[user_id]
        
        # Calculate account age
        account_age = (datetime.now() - user['created_at']).days
        
        # Prepare user profile
        user_profile = {
            'account_age_days': account_age,
            'followers_count': user['followers_count'],
            'posts_count': user['posts_count']
        }
        
        # Get conversation history
        conversation_history = conversation_tracker.get_history(user_id)
        
        # ⚡ RUN SAFETY ANALYSIS
        analysis_result = safety_analyzer.analyze_message(
            message_text,
            user_profile,
            conversation_history
        )
        
        # Add to conversation history
        conversation_tracker.add_message(user_id, message_text)
        
        # Update user stats
        user['messages_sent'] += 1
        if analysis_result['action'] in ['warn', 'hide']:
            user['warnings_received'] += 1
        
        # Handle blocking
        if analysis_result['action'] == 'block':
            blocked_users.add(user_id)
            user['is_blocked'] = True
            analysis_result['blocked'] = True
        
        # Log message
        messages_log.append({
            'user_id': user_id,
            'username': username,
            'message': message_text,
            'risk_score': analysis_result['risk_score'],
            'action': analysis_result['action'],
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'risk_score': analysis_result['risk_score'],
            'risk_level': analysis_result['risk_level'],
            'categories': analysis_result['categories'],
            'reasons': analysis_result['reasons'],
            'action': analysis_result['action'],
            'should_escalate': analysis_result['should_escalate'],
            'blocked': analysis_result.get('blocked', False),
            'details': analysis_result['details'],
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- STATISTICS & MONITORING ---

@app.route('/api/stats/overview', methods=['GET'])
def stats_overview():
    """Get system statistics"""
    try:
        total_messages = len(messages_log)
        blocked_count = len(blocked_users)
        
        risk_breakdown = {'Safe': 0, 'Warning': 0, 'Dangerous': 0, 'Critical': 0}
        for msg in messages_log:
            # Recalculate based on action (simplified)
            if msg['risk_score'] <= 30:
                risk_breakdown['Safe'] += 1
            elif msg['risk_score'] <= 60:
                risk_breakdown['Warning'] += 1
            elif msg['risk_score'] <= 80:
                risk_breakdown['Dangerous'] += 1
            else:
                risk_breakdown['Critical'] += 1
        
        return jsonify({
            'total_messages_analyzed': total_messages,
            'blocked_users_count': blocked_count,
            'risk_breakdown': risk_breakdown,
            'total_users': len(users_db),
            'blocked_users_list': list(blocked_users)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats/user/<user_id>', methods=['GET'])
def user_stats(user_id):
    """Get individual user stats"""
    try:
        if user_id not in users_db:
            return jsonify({'error': 'User not found'}), 404
        
        user = users_db[user_id]
        history = conversation_tracker.get_history(user_id)
        
        return jsonify({
            'user_id': user_id,
            'username': user['username'],
            'messages_sent': user['messages_sent'],
            'warnings_received': user['warnings_received'],
            'is_blocked': user['is_blocked'],
            'account_age_days': (datetime.now() - user['created_at']).days,
            'recent_messages': history[-5:],
            'message_count': len(history)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- TESTING & DEMO ---

@app.route('/api/demo/test_messages', methods=['GET'])
def demo_test_messages():
    """Get test messages for demo"""
    return jsonify({
        'test_messages': [
            {
                'type': 'safe',
                'text': 'Hey! How are you doing today?',
                'expected_action': 'allow',
                'description': 'Normal, safe conversation'
            },
            {
                'type': 'love_bombing',
                'text': 'You are my soulmate, I love you so much!',
                'expected_action': 'warn',
                'description': 'Love bombing pattern (+15)'
            },
            {
                'type': 'financial_urgent',
                'text': 'I need urgent help! Send me money to my bank account right now!',
                'expected_action': 'hide',
                'description': 'Urgency + Financial request combined (+70)'
            },
            {
                'type': 'isolation',
                'text': "Don't tell anyone about this, keep it secret between us",
                'expected_action': 'warn',
                'description': 'Isolation phrase (+25)'
            },
            {
                'type': 'escalation',
                'text': 'My soulmate, you are the only one who understands me. Please send me money urgently!',
                'expected_action': 'block',
                'description': 'Love + Isolation + Money escalation (+95)'
            },
            {
                'type': 'vulgar',
                'text': 'You are so stupid and pathetic, I hate you!',
                'expected_action': 'warn',
                'description': 'Abusive language (+20)'
            }
        ]
    }), 200


@app.route('/api/demo/create_sample_users', methods=['POST'])
def create_sample_users():
    """Create sample users for demo"""
    try:
        sample_users = [
            {'username': 'Honest User', 'followers_count': 50, 'posts_count': 25},
            {'username': 'Scammer (New)', 'followers_count': 0, 'posts_count': 0},
            {'username': 'Bot Account', 'followers_count': 5, 'posts_count': 0},
        ]
        
        created = []
        for user_data in sample_users:
            response = create_user.__wrapped__(
                Flask.test_request_context(
                    json=user_data,
                    method='POST'
                ).request
            )
            # Manual creation instead
            user_id = f"demo_{len(users_db)}"
            users_db[user_id] = {
                'user_id': user_id,
                'username': user_data['username'],
                'created_at': datetime.now(),
                'followers_count': user_data.get('followers_count', 0),
                'posts_count': user_data.get('posts_count', 0),
                'is_blocked': False,
                'messages_sent': 0,
                'warnings_received': 0
            }
            conversation_tracker.init_user(user_id)
            created.append({'user_id': user_id, 'username': user_data['username']})
        
        return jsonify({'created': created}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- HEALTH CHECK ---

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'OK', 'service': 'SafeChat Backend'}), 200


# ==================== MAIN ====================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🛡️  SAFECHAT - BACKEND SAFETY SYSTEM")
    print("="*60)
    print("\n📍 Running on: http://localhost:5000")
    print("\n📚 API Endpoints:")
    print("   POST   /api/analyze_message → Analyze message")
    print("   POST   /api/users/create → Create user")
    print("   GET    /api/users/<user_id> → Get user info")
    print("   GET    /api/stats/overview → System stats")
    print("   GET    /api/stats/user/<user_id> → User stats")
    print("   GET    /api/demo/test_messages → Demo messages")
    print("   GET    /health → Health check")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')