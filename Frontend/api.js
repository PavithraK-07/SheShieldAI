const API_BASE = 'http://localhost:5000/api';

class ChatAPI {
    static async createUser(username, followers_count = 0, posts_count = 0) {
        try {
            const response = await fetch(`${API_BASE}/users/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username,
                    followers_count,
                    posts_count
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error creating user:', error);
            throw error;
        }
    }

    static async getUser(user_id) {
        try {
            const response = await fetch(`${API_BASE}/users/${user_id}`);
            return await response.json();
        } catch (error) {
            console.error('Error getting user:', error);
            throw error;
        }
    }

    static async analyzeMessage(message, user_id, username) {
        try {
            const response = await fetch(`${API_BASE}/analyze_message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    user_id,
                    username
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error analyzing message:', error);
            throw error;
        }
    }

    static async getStats() {
        try {
            const response = await fetch(`${API_BASE}/stats/overview`);
            return await response.json();
        } catch (error) {
            console.error('Error getting stats:', error);
            throw error;
        }
    }

    static async getUserStats(user_id) {
        try {
            const response = await fetch(`${API_BASE}/stats/user/${user_id}`);
            return await response.json();
        } catch (error) {
            console.error('Error getting user stats:', error);
            throw error;
        }
    }

    static async getTestMessages() {
        try {
            const response = await fetch(`${API_BASE}/demo/test_messages`);
            return await response.json();
        } catch (error) {
            console.error('Error getting test messages:', error);
            throw error;
        }
    }

    static async createSampleUsers() {
        try {
            const response = await fetch(`${API_BASE}/demo/create_sample_users`, {
                method: 'POST'
            });
            return await response.json();
        } catch (error) {
            console.error('Error creating sample users:', error);
            throw error;
        }
    }
}