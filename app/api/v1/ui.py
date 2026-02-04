"""Simple HTML UI endpoints for MVP testing."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(prefix="/ui", tags=["UI"], include_in_schema=False)

# Simple HTML template for draft reply UI
DRAFT_UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Support Assistant - Draft Replies</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; margin-bottom: 20px; }
        .ticket-card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .ticket-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .ticket-subject { font-size: 18px; font-weight: 600; color: #333; }
        .ticket-meta { color: #666; font-size: 14px; }
        .ticket-content { background: #f9f9f9; padding: 15px; border-radius: 4px; margin-bottom: 15px; white-space: pre-wrap; }
        .draft-section { border-top: 1px solid #eee; padding-top: 15px; }
        .draft-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .confidence { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .confidence.high { background: #d4edda; color: #155724; }
        .confidence.medium { background: #fff3cd; color: #856404; }
        .confidence.low { background: #f8d7da; color: #721c24; }
        .confidence.very_low { background: #721c24; color: white; }
        .draft-reply { width: 100%; min-height: 150px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; font-family: inherit; font-size: 14px; resize: vertical; }
        .recommendations { background: #fff3cd; padding: 10px; border-radius: 4px; margin: 10px 0; font-size: 13px; }
        .recommendations ul { margin-left: 20px; }
        .btn-group { display: flex; gap: 10px; margin-top: 15px; }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: 500; }
        .btn-primary { background: #007bff; color: white; }
        .btn-primary:hover { background: #0056b3; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-warning { background: #ffc107; color: #333; }
        .stats { display: flex; gap: 20px; margin-bottom: 10px; font-size: 13px; color: #666; }
        .no-draft { color: #666; font-style: italic; }
        .escalate-warning { background: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 4px; margin: 10px 0; color: #721c24; }
        .intent-badge { background: #e9ecef; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
        .login-form { max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 8px; }
        .login-form input { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px; }
        .login-form button { width: 100%; }
    </style>
</head>
<body>
    <div class="container">
        <h1>AI Support Assistant</h1>
        <p style="color: #666; margin-bottom: 20px;">Review and approve AI-generated draft replies</p>

        <div id="login-section" class="login-form">
            <h2 style="margin-bottom: 20px;">Login</h2>
            <input type="email" id="email" placeholder="Email" required>
            <input type="password" id="password" placeholder="Password" required>
            <button class="btn btn-primary" onclick="login()">Login</button>
            <p id="login-error" style="color: red; margin-top: 10px; display: none;"></p>
        </div>

        <div id="main-section" style="display: none;">
            <div style="margin-bottom: 20px;">
                <button class="btn btn-secondary" onclick="syncTickets()">Sync from WHMCS</button>
                <button class="btn btn-primary" onclick="loadPendingTickets()">Refresh</button>
                <span id="sync-status" style="margin-left: 10px; color: #666;"></span>
            </div>

            <div id="tickets-container">
                <p>Loading tickets...</p>
            </div>
        </div>
    </div>

    <script>
        let token = localStorage.getItem('token');

        if (token) {
            document.getElementById('login-section').style.display = 'none';
            document.getElementById('main-section').style.display = 'block';
            loadPendingTickets();
        }

        async function login() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            try {
                const formData = new FormData();
                formData.append('username', email);
                formData.append('password', password);

                const res = await fetch('/api/v1/auth/login', {
                    method: 'POST',
                    body: formData
                });

                if (!res.ok) throw new Error('Invalid credentials');

                const data = await res.json();
                token = data.access_token;
                localStorage.setItem('token', token);

                document.getElementById('login-section').style.display = 'none';
                document.getElementById('main-section').style.display = 'block';
                loadPendingTickets();
            } catch (e) {
                document.getElementById('login-error').textContent = e.message;
                document.getElementById('login-error').style.display = 'block';
            }
        }

        async function apiCall(url, method = 'GET', body = null) {
            const options = {
                method,
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            };
            if (body) options.body = JSON.stringify(body);

            const res = await fetch(url, options);
            if (res.status === 401) {
                localStorage.removeItem('token');
                location.reload();
            }
            return res;
        }

        async function syncTickets() {
            document.getElementById('sync-status').textContent = 'Syncing...';
            try {
                const res = await apiCall('/api/v1/whmcs/sync', 'POST', { limit: 25 });
                const data = await res.json();
                document.getElementById('sync-status').textContent = `Synced ${data.synced_count} tickets`;
                loadPendingTickets();
            } catch (e) {
                document.getElementById('sync-status').textContent = 'Sync failed';
            }
        }

        async function loadPendingTickets() {
            const container = document.getElementById('tickets-container');
            container.innerHTML = '<p>Loading...</p>';

            try {
                const res = await apiCall('/api/v1/whmcs/tickets/pending?limit=20');
                const tickets = await res.json();

                if (tickets.length === 0) {
                    container.innerHTML = '<p>No pending tickets. Sync from WHMCS to get started.</p>';
                    return;
                }

                container.innerHTML = tickets.map(t => renderTicketCard(t)).join('');
            } catch (e) {
                container.innerHTML = '<p>Error loading tickets</p>';
            }
        }

        function renderTicketCard(ticket) {
            return `
                <div class="ticket-card" id="ticket-${ticket.id}">
                    <div class="ticket-header">
                        <div>
                            <div class="ticket-subject">${escapeHtml(ticket.subject)}</div>
                            <div class="ticket-meta">
                                #${ticket.whmcs_ticket_id} | ${ticket.department || 'General'} | ${ticket.priority || 'Normal'} | ${ticket.client_email || ''}
                            </div>
                        </div>
                        <span class="intent-badge">${ticket.status}</span>
                    </div>
                    <div class="ticket-content">${escapeHtml(ticket.content)}</div>
                    <div class="draft-section" id="draft-${ticket.id}">
                        ${ticket.has_ai_reply ? '<p>Loading draft...</p>' : `
                            <p class="no-draft">No AI draft yet</p>
                            <button class="btn btn-primary" onclick="generateDraft(${ticket.id})">Generate AI Draft</button>
                        `}
                    </div>
                </div>
            `;
        }

        async function generateDraft(ticketId) {
            const draftSection = document.getElementById(`draft-${ticketId}`);
            draftSection.innerHTML = '<p>Generating draft... (this may take a few seconds)</p>';

            try {
                const res = await apiCall('/api/v1/replies/generate', 'POST', {
                    ticket_id: ticketId,
                    use_reranking: true
                });

                if (!res.ok) throw new Error('Failed to generate');

                const draft = await res.json();
                draftSection.innerHTML = renderDraft(ticketId, draft);
            } catch (e) {
                draftSection.innerHTML = `<p style="color: red;">Error: ${e.message}</p>
                    <button class="btn btn-primary" onclick="generateDraft(${ticketId})">Retry</button>`;
            }
        }

        function renderDraft(ticketId, draft) {
            const levelClass = draft.confidence_level.toLowerCase();
            const recommendations = draft.recommendations || [];

            return `
                <div class="draft-header">
                    <strong>AI Draft Reply</strong>
                    <span class="confidence ${levelClass}">
                        ${draft.confidence_score.toFixed(1)}% - ${draft.confidence_level}
                    </span>
                </div>
                <div class="stats">
                    <span>Intent: <strong>${draft.intent_detected || 'general'}</strong></span>
                    <span>Tokens: ${draft.tokens_used}</span>
                    <span>Latency: ${draft.latency_ms}ms</span>
                </div>
                ${draft.should_escalate ? '<div class="escalate-warning">⚠️ Low confidence - Consider escalating this ticket</div>' : ''}
                ${recommendations.length > 0 ? `
                    <div class="recommendations">
                        <strong>Recommendations:</strong>
                        <ul>${recommendations.map(r => `<li>${escapeHtml(r)}</li>`).join('')}</ul>
                    </div>
                ` : ''}
                <textarea class="draft-reply" id="reply-${ticketId}">${escapeHtml(draft.ai_reply)}</textarea>
                <div class="btn-group">
                    <button class="btn btn-success" onclick="approveReply(${ticketId}, ${draft.id})">Approve & Send</button>
                    <button class="btn btn-secondary" onclick="generateDraft(${ticketId})">Regenerate</button>
                </div>
            `;
        }

        async function approveReply(ticketId, aiReplyId) {
            const finalReply = document.getElementById(`reply-${ticketId}`).value;

            try {
                const res = await apiCall('/api/v1/replies/approve', 'POST', {
                    ai_reply_id: aiReplyId,
                    final_reply: finalReply
                });

                if (!res.ok) throw new Error('Failed to approve');

                const data = await res.json();
                const card = document.getElementById(`ticket-${ticketId}`);
                card.innerHTML = `
                    <div style="padding: 20px; text-align: center; color: #28a745;">
                        <h3>✓ Reply Approved</h3>
                        <p>${data.edited ? '(with edits)' : '(no edits)'} ${data.is_correction ? '- Marked as correction' : ''}</p>
                    </div>
                `;

                setTimeout(() => card.remove(), 3000);
            } catch (e) {
                alert('Error approving reply: ' + e.message);
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text || '';
            return div.innerHTML;
        }
    </script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
async def draft_reply_ui():
    """Simple HTML UI for reviewing and approving AI draft replies."""
    return DRAFT_UI_TEMPLATE
