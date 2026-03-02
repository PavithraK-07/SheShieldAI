"""
Fake Account Detection System
"""

class FakeAccountDetector:
    def __init__(self):
        pass
    
    def calculate_trust_score(self, user_profile):
        """
        Calculate trust score for an account
        Returns: 0-100 (100 = most trustworthy)
        """
        trust_score = 100
        
        # Account age
        account_age = user_profile.get('account_age_days', 0)
        if account_age < 1:
            trust_score -= 40
        elif account_age < 7:
            trust_score -= 30
        elif account_age < 30:
            trust_score -= 15
        
        # Social presence
        followers = user_profile.get('followers_count', 0)
        posts = user_profile.get('posts_count', 0)
        
        if followers == 0 and posts == 0:
            trust_score -= 30
        elif posts == 0 and followers > 50:
            trust_score -= 20  # Bot-like
        
        # Engagement
        if posts > 0:
            engagement_ratio = followers / max(posts, 1)
            if engagement_ratio > 10:
                trust_score -= 10  # Unnatural ratio
        
        return max(0, min(100, trust_score))
    
    def is_likely_fake(self, user_profile):
        """Check if account is likely fake"""
        trust_score = self.calculate_trust_score(user_profile)
        return trust_score < 40