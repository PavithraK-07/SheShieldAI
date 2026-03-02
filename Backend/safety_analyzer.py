"""
🛡️ Core Safety Analyzer
Rule-based threat detection system
"""

class SafetyAnalyzer:
    def __init__(self):
        # Define threat keywords and scoring
        self.threat_patterns = {
            'abusive_vulgar': {
                'keywords': [
                    'stupid', 'idiot', 'hate you', 'die', 'kill yourself',
                    'worthless', 'garbage', 'trash', 'ugly', 'pathetic',
                    'loser', 'asshole', 'bitch', 'bastard', 'damn', 'hell'
                ],
                'score': 20,
                'category': 'Harassment'
            },
            
            'love_bombing': {
                'keywords': [
                    'soulmate', 'marry me', 'marry me quickly', 'love you',
                    'you are my only one', 'only you understand',
                    'perfect match', 'meant to be', 'love at first sight',
                    'you complete me', 'forever together', 'my everything',
                    'angel', 'beautiful soul', 'divine connection', 'i adore you'
                ],
                'score': 15,
                'category': 'Romance Scam'
            },
            
            'urgency_words': {
                'keywords': [
                    'urgent', 'immediately', 'emergency', 'asap', 'right now',
                    'quickly', 'hurry', 'no time', 'fast', 'at once',
                    'this instant', 'without delay', 'time sensitive', 'rush'
                ],
                'score': 10,
                'category': 'Urgency'
            },
            
            'financial_requests': {
                'keywords': [
                    'send money', 'transfer', 'bank details', 'account number',
                    'routing number', 'credit card', 'pay me', 'wire transfer',
                    'gift card', 'crypto', 'bitcoin', 'payment', 'cash',
                    'financial help', 'money urgent', 'need cash', 'loan',
                    'invest', 'upfront payment', 'processing fee', 'verify account'
                ],
                'score': 25,
                'category': 'Financial Exploitation'
            },
            
            'isolation_phrases': {
                'keywords': [
                    "don't tell anyone", 'keep this secret', 'only you understand',
                    'nobody knows about', 'dont talk about this', 'secret between us',
                    'private', 'confidential', 'dont share', 'private conversation',
                    'tell no one', 'between you and me', 'just us'
                ],
                'score': 25,
                'category': 'Grooming'
            }
        }
        
        # Escalation patterns
        self.escalation_patterns = [
            {
                'name': 'Romance to Money',
                'sequence': ['love_bombing', 'isolation_phrases', 'financial_requests'],
                'bonus_score': 30
            },
            {
                'name': 'Grooming Escalation',
                'sequence': ['love_bombing', 'isolation_phrases'],
                'bonus_score': 20
            },
            {
                'name': 'Urgent Financial',
                'sequence': ['urgency_words', 'financial_requests'],
                'bonus_score': 30
            }
        ]
    
    def analyze_message(self, message_text, user_profile, conversation_history):
        """
        Main analysis function
        Returns: {risk_score, risk_level, categories, reasons, action, should_escalate, details}
        """
        risk_score = 0
        reasons = []
        categories_found = set()
        
        # ========== MESSAGE CONTENT ANALYSIS ==========
        
        threat_details = self._check_threats(message_text)
        risk_score += threat_details['score']
        reasons.extend(threat_details['reasons'])
        categories_found.update(threat_details['categories'])
        
        # Combined patterns
        combined_score = self._check_combined_patterns(message_text)
        if combined_score > 0:
            risk_score += combined_score
            reasons.append(f"⚠️ Dangerous pattern combination (+{combined_score})")
        
        # ========== ACCOUNT PROFILE ANALYSIS ==========
        
        fake_account_score = self._analyze_account_risk(user_profile)
        if fake_account_score > 0:
            risk_score += fake_account_score
            reasons.append(f"🚩 Suspicious account profile (+{fake_account_score})")
            categories_found.add('Fake Account')
        
        # ========== CONVERSATION ESCALATION ==========
        
        escalation_score = self._check_escalation_patterns(
            message_text, 
            conversation_history
        )
        if escalation_score > 0:
            risk_score += escalation_score
            reasons.append(f"📈 Conversation escalation detected (+{escalation_score})")
        
        # ========== DETERMINE ACTION ==========
        
        risk_level = self._get_risk_level(risk_score)
        action = self._get_action(risk_score)
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'categories': list(categories_found),
            'reasons': reasons,
            'action': action,
            'should_escalate': escalation_score > 0,
            'details': {
                'message_threat_score': threat_details['score'],
                'account_risk_score': fake_account_score,
                'escalation_score': escalation_score,
                'combined_pattern_score': combined_score
            }
        }
    
    def _check_threats(self, message_text):
        """Check for threat keywords"""
        text_lower = message_text.lower()
        total_score = 0
        reasons = []
        categories = set()
        
        for threat_type, threat_data in self.threat_patterns.items():
            threat_score = 0
            found_keywords = []
            
            for keyword in threat_data['keywords']:
                if keyword.lower() in text_lower:
                    threat_score += threat_data['score']
                    found_keywords.append(keyword)
            
            if threat_score > 0:
                total_score += threat_score
                categories.add(threat_data['category'])
                keywords_str = ', '.join(found_keywords[:2])
                reasons.append(
                    f"🚨 {threat_type.replace('_', ' ').title()}: "
                    f"'{keywords_str}' (+{threat_score})"
                )
        
        return {
            'score': total_score,
            'reasons': reasons,
            'categories': categories
        }
    
    def _check_combined_patterns(self, message_text):
        """Check dangerous combinations"""
        text_lower = message_text.lower()
        bonus_score = 0
        
        # Urgency + Financial
        has_urgency = any(
            kw in text_lower 
            for kw in self.threat_patterns['urgency_words']['keywords']
        )
        has_money = any(
            kw in text_lower 
            for kw in self.threat_patterns['financial_requests']['keywords']
        )
        
        if has_urgency and has_money:
            bonus_score += 40
        
        # Love Bombing + Isolation
        has_love = any(
            kw in text_lower 
            for kw in self.threat_patterns['love_bombing']['keywords']
        )
        has_isolation = any(
            kw in text_lower 
            for kw in self.threat_patterns['isolation_phrases']['keywords']
        )
        
        if has_love and has_isolation:
            bonus_score += 30
        
        return bonus_score
    
    def _analyze_account_risk(self, user_profile):
        """Analyze account for fake indicators"""
        score = 0
        
        # New account (<7 days)
        if user_profile.get('account_age_days', 0) < 7:
            score += 30
        elif user_profile.get('account_age_days', 0) < 30:
            score += 15
        
        # No followers + no posts
        if user_profile.get('followers_count', 0) == 0 and \
           user_profile.get('posts_count', 0) == 0:
            score += 20
        
        # High followers to post ratio (bot)
        followers = user_profile.get('followers_count', 0)
        posts = user_profile.get('posts_count', 0)
        if posts == 0 and followers > 100:
            score += 15
        
        return score
    
    def _check_escalation_patterns(self, current_message, conversation_history):
        """Detect escalation patterns in conversation"""
        if not conversation_history or len(conversation_history) < 2:
            return 0
        
        # Map conversation to threat types
        conversation_threats = []
        for msg in conversation_history[-10:]:
            text_lower = msg.lower()
            
            for threat_type, threat_data in self.threat_patterns.items():
                if any(kw in text_lower for kw in threat_data['keywords']):
                    conversation_threats.append(threat_type)
                    break
        
        # Add current message
        text_lower = current_message.lower()
        for threat_type, threat_data in self.threat_patterns.items():
            if any(kw in text_lower for kw in threat_data['keywords']):
                conversation_threats.append(threat_type)
                break
        
        # Check patterns
        escalation_score = 0
        for pattern in self.escalation_patterns:
            pattern_seq = pattern['sequence']
            if self._find_sequence(conversation_threats, pattern_seq):
                escalation_score += pattern['bonus_score']
        
        return escalation_score
    
    def _find_sequence(self, conversation_threats, pattern_sequence):
        """Check if sequence exists in conversation"""
        if len(pattern_sequence) > len(conversation_threats):
            return False
        
        for i in range(len(conversation_threats) - len(pattern_sequence) + 1):
            if conversation_threats[i:i+len(pattern_sequence)] == pattern_sequence:
                return True
        
        return False
    
    def _get_risk_level(self, risk_score):
        """Convert score to level"""
        if risk_score <= 30:
            return 'Safe'
        elif risk_score <= 60:
            return 'Warning'
        elif risk_score <= 80:
            return 'Dangerous'
        else:
            return 'Critical'
    
    def _get_action(self, risk_score):
        """Determine action"""
        if risk_score <= 30:
            return 'allow'
        elif risk_score <= 60:
            return 'warn'
        elif risk_score <= 80:
            return 'hide'
        else:
            return 'block'