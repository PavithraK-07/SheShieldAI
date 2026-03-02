let users = [];
let currentUser = null;
let chatMessages = {};
let pendingMessage = null;

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    document.getElementById('messageInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            sendMessage();
        }
    });
}

// ==================== USER MANAGEMENT ====================

async function setupDemoUsers() {
    try {
        const result = await ChatAPI.createSampleUsers();
        if (result.created) {
            users = result.created;
            renderUsersList();
            alert('✅ Demo users created!');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function createNewUser() {
    const username = document.getElementById('newUsername').value.trim();
    const followers = parseInt(document.getElementById('newFollowers').value) || 0;
    const posts = parseInt(document.getElementById('newPosts').value) || 0;

    if (!username) {
        alert('Please enter a username');
        return;
    }

    try {
        const result = await ChatAPI.createUser(username, followers, posts);
        users.push(result);
        renderUsersList();
        closeModal('newUserModal');
        alert(`✅ User ${username} created!`);
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function addNewUser() {
    openModal('newUserModal');
}

function renderUsersList() {
    const container = document.getElementById('usersList');
    container.innerHTML = users.map(user => `
        <div class="user-item ${currentUser?.user_id === user.user_id ? 'active' : ''}" 
             onclick="selectUser('${user.user_id}', '${user.username}')">
            <div>${user.username}</div>
            <div class="user-status">ID: ${user.user_id.substring(0, 8)}...</div>
        </div>
    `).join('');
}

function selectUser(user_id, username) {
    currentUser = { user_id, username };
    
    // Initialize chat
    if (!chatMessages[user_id]) {
        chatMessages[user_id] = [];
    }
    
    // Update UI
    renderUsersList();
    document.getElementById('chatHeaderContent').textContent = `💬 Chat with ${username}`;
    document.getElementById('messagesArea').innerHTML = '';
    document.getElementById('messageInput').disabled = false;
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('messageInput').focus();
    document.getElementById('analysisContent').innerHTML = '<p>Send a message to see analysis</p>';
}

// ==================== MESSAGING ====================

async function sendMessage() {
    const messageText = document.getElementById('messageInput').value.trim();
    
    if (!messageText) return;
    if (!currentUser) {
        alert('Please select a user first');
        return;
    }
    
    const sendBtn = document.getElementById('sendBtn');
    const messageInput = document.getElementById('messageInput');
    
    sendBtn.disabled = true;
    sendBtn.textContent = '⏳ Analyzing...';
    messageInput.disabled = true;
    
    try {
        // Analyze message
        const analysis = await ChatAPI.analyzeMessage(
            messageText,
            currentUser.user_id,
            currentUser.username
        );
        
        // Handle different actions
        if (analysis.blocked) {
            showBlockModal(analysis);
            messageInput.value = '';
        } else if (analysis.action === 'hide') {
            pendingMessage = { text: messageText, analysis };
            showWarningModal(analysis, messageText);
        } else if (analysis.action === 'warn') {
            pendingMessage = { text: messageText, analysis };
            showWarningModal(analysis, messageText);
        } else {
            // Safe - add immediately
            addMessageToChat(messageText, analysis);
            displayAnalysis(analysis);
            messageInput.value = '';
        }
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send';
        messageInput.disabled = false;
    }
}

function addMessageToChat(text, analysis) {
    if (!currentUser) return;
    
    const msg = {
        text,
        analysis,
        timestamp: new Date()
    };
    
    chatMessages[currentUser.user_id].push(msg);
    renderMessages();
}

function renderMessages() {
    if (!currentUser) return;
    
    const messagesContainer = document.getElementById('messagesArea');
    const messages = chatMessages[currentUser.user_id] || [];
    
    if (messages.length === 0) {
        messagesContainer.innerHTML = '<div style="color: #999; text-align: center; padding: 40px;">No messages yet</div>';
        return;
    }
    
    messagesContainer.innerHTML = messages.map(msg => {
        const riskClass = msg.analysis.risk_level.toLowerCase();
        const shouldShowAnalysis = msg.analysis.action !== 'allow';
        
        return `
            <div class="message sent">
                <div class="message-bubble">
                    <div class="message-text">${escapeHtml(msg.text)}</div>
                    ${shouldShowAnalysis ? `
                        <div class="message-analysis ${msg.analysis.action === 'block' ? 'danger' : 'warning'}">
                            <strong>${msg.analysis.risk_level}</strong> (${msg.analysis.risk_score})
                        </div>
                    ` : ''}
                    <div class="message-time">${msg.timestamp.toLocaleTimeString()}</div>
                </div>
            </div>
        `;
    }).join('');
    
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function displayAnalysis(analysis) {
    const panel = document.getElementById('analysisContent');
    const reasonsList = analysis.reasons
        .map(r => `<li>${escapeHtml(r)}</li>`)
        .join('');
    
    panel.innerHTML = `
        <div class="analysis-item">
            <div class="analysis-label">Risk Score</div>
            <div class="risk-score ${analysis.risk_level.toLowerCase()}">
                ${analysis.risk_score} / 100 (${analysis.risk_level})
            </div>
        </div>
        
        <div class="analysis-item">
            <div class="analysis-label">Categories</div>
            <p>${analysis.categories.length > 0 ? analysis.categories.join(', ') : 'None'}</p>
        </div>
        
        <div class="analysis-item">
            <div class="analysis-label">Reasons</div>
            <ul class="reason-list">
                ${reasonsList || '<li>Message is safe</li>'}
            </ul>
        </div>
        
        <div class="analysis-item">
            <div class="analysis-label">Action</div>
            <p><strong>${analysis.action.toUpperCase()}</strong></p>
        </div>
    `;
}

// ==================== MODALS ====================

function openModal(modalId) {
    document.getElementById(modalId).classList.add('show');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}

function showWarningModal(analysis, messageText) {
    const content = document.getElementById('warningContent');
    const reasonsList = analysis.reasons
        .map(r => `<li>${escapeHtml(r)}</li>`)
        .join('');
    
    content.innerHTML = `
        <div style="background: #fff3cd; padding: 12px; border-radius: 8px; margin-bottom: 15px;">
            <strong>⚠️ This message might be risky!</strong>
        </div>
        <p><strong>Message:</strong> "${escapeHtml(messageText)}"</p>
        <p><strong>Risk Score:</strong> ${analysis.risk_score} / 100</p>
        <p><strong>Level:</strong> ${analysis.risk_level}</p>
        <p><strong>Categories:</strong> ${analysis.categories.join(', ') || 'None'}</p>
        <p><strong>Reasons:</strong></p>
        <ul style="margin-left: 15px; margin-bottom: 15px;">
            ${reasonsList}
        </ul>
    `;
    
    openModal('warningModal');
}

function confirmMessage() {
    if (pendingMessage) {
        addMessageToChat(pendingMessage.text, pendingMessage.analysis);
        displayAnalysis(pendingMessage.analysis);
        document.getElementById('messageInput').value = '';
        pendingMessage = null;
    }
    closeModal('warningModal');
}

function cancelMessage() {
    pendingMessage = null;
    closeModal('warningModal');
}

function showBlockModal(analysis) {
    const content = document.getElementById('blockContent');
    const reasonsList = analysis.reasons
        .map(r => `<li>${escapeHtml(r)}</li>`)
        .join('');
    
    content.innerHTML = `
        <div style="background: #f8d7da; padding: 12px; border-radius: 8px; margin-bottom: 15px;">
            <strong>🚫 User has been BLOCKED</strong>
        </div>
        <p><strong>Risk Score:</strong> ${analysis.risk_score} / 100 (CRITICAL)</p>
        <p><strong>Category:</strong> ${analysis.categories.join(', ')}</p>
        <p><strong>Reasons:</strong></p>
        <ul style="margin-left: 15px; margin-bottom: 15px;">
            ${reasonsList}
        </ul>
        <p style="color: #721c24; font-size: 13px;">
            This message violates safety policies. The user has been blocked.
        </p>
    `;
    
    openModal('blockModal');
}

async function openStats() {
    try {
        const stats = await ChatAPI.getStats();
        const statsContent = document.getElementById('statsContent');
        
        const riskBreakdown = Object.entries(stats.risk_breakdown)
            .map(([level, count]) => `<li>${level}: ${count}</li>`)
            .join('');
        
        statsContent.innerHTML = `
            <div class="analysis-item">
                <div class="analysis-label">Total Messages</div>
                <p><strong>${stats.total_messages_analyzed}</strong></p>
            </div>
            
            <div class="analysis-item">
                <div class="analysis-label">Total Users</div>
                <p><strong>${stats.total_users}</strong></p>
            </div>
            
            <div class="analysis-item">
                <div class="analysis-label">Blocked Users</div>
                <p><strong>${stats.blocked_users_count}</strong></p>
                ${stats.blocked_users_list.length > 0 ? `
                    <ul class="reason-list">
                        ${stats.blocked_users_list.map(u => `<li>${u}</li>`).join('')}
                    </ul>
                ` : '<p>None</p>'}
            </div>
            
            <div class="analysis-item">
                <div class="analysis-label">Risk Breakdown</div>
                <ul class="reason-list">
                    ${riskBreakdown}
                </ul>
            </div>
        `;
        
        openModal('statsModal');
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function showTestMessages() {
    try {
        const data = await ChatAPI.getTestMessages();
        const container = document.getElementById('testMessagesContainer');
        
        container.innerHTML = data.test_messages.map((msg, idx) => `
            <div style="margin-bottom: 15px; padding: 12px; background: #f5f5f5; border-radius: 8px;">
                <p><strong>${idx + 1}. ${msg.description}</strong></p>
                <p style="color: #666; font-style: italic; margin: 8px 0;">
                    "${msg.text}"
                </p>
                <p><small>Expected: <strong>${msg.expected_action.toUpperCase()}</strong></small></p>
                <button class="btn btn-small btn-primary" 
                    onclick="useTestMessage('${msg.text.replace(/'/g, "\\'")}')">
                    Use This
                </button>
            </div>
        `).join('');
        
        openModal('testModal');
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function useTestMessage(text) {
    if (!currentUser) {
        alert('Please select a user first');
        return;
    }
    document.getElementById('messageInput').value = text;
    document.getElementById('messageInput').focus();
    closeModal('testModal');
}

// ==================== UTILITIES ====================

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}