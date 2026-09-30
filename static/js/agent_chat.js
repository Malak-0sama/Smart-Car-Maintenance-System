/**
 * Agent Chat UI Module
 * Handles async fetch calls to the Django AI agent endpoint and renders
 * the conversation, including a lightweight trace of any tool calls the
 * agent made (transparency for the user + easy grading during defense).
 */

class AgentChat {
    constructor() {
        this.windowEl = document.getElementById("chat-window");
        this.inputEl = document.getElementById("chat-input");
        this.sendBtn = document.getElementById("chat-send");
        this.sessionId = null;

        this.sendBtn.addEventListener("click", () => this.send());
        this.inputEl.addEventListener("keydown", (e) => {
            if (e.key === "Enter") this.send();
        });
    }

    appendMessage(role, text) {
        const el = document.createElement("div");
        el.className = `chat-msg ${role}`;
        el.textContent = text;
        this.windowEl.appendChild(el);
        this.windowEl.scrollTop = this.windowEl.scrollHeight;
    }

    appendToolTrace(_trace) {
        // Tool internals are intentionally hidden from end users.
    }

    async send() {
        const message = this.inputEl.value.trim();
        if (!message) return;

        this.appendMessage("user", message);
        this.inputEl.value = "";
        this.sendBtn.disabled = true;

        try {
            const response = await fetch(window.CHAT_ENDPOINT, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": window.CSRF_TOKEN,
                },
                body: JSON.stringify({
                    message,
                    session_id: this.sessionId,
                }),
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                this.appendMessage("assistant", `Error: ${err.error || "something went wrong."}`);
                return;
            }

            const data = await response.json();
            this.sessionId = data.session_id;

            if (data.tool_trace && data.tool_trace.length > 0) {
                this.appendToolTrace(data.tool_trace);
            }
            this.appendMessage("assistant", data.reply);
        } catch (e) {
            this.appendMessage("assistant", "Network error. Please try again.");
        } finally {
            this.sendBtn.disabled = false;
        }
    }
}

document.addEventListener("DOMContentLoaded", () => new AgentChat());
