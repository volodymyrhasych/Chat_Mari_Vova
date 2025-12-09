from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, create_engine, Session, select

# ---------- FastAPI app ----------
app = FastAPI(title="Mini Chat for Volodymyr & Mari")

# ---------- База даних (SQLite) ----------

DATABASE_URL = "sqlite:///chat.db"
engine = create_engine(DATABASE_URL, echo=False)


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sender: str
    text: str
    timestamp: datetime


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


# ---------- Pydantic-схеми для API ----------

class MessageIn(BaseModel):
    sender: str
    text: str


class MessageOut(BaseModel):
    sender: str
    text: str
    timestamp: str


# ---------- HTML-чат ----------

CHAT_HTML = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8" />
    <title>Mini Chat for Volodymyr & Mari</title>
    <style>
        body {
            margin: 0;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
            background: radial-gradient(circle at top, #1f2933 0, #020617 55%, #020617 100%);
            color: #e5e7eb;
        }
        .card {
            width: 420px;
            background: rgba(10, 16, 30, 0.95);
            border-radius: 24px;
            box-shadow:
                0 20px 60px rgba(0,0,0,0.8),
                0 0 0 1px rgba(148, 163, 184, 0.08);
            padding: 20px 22px 18px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .header-title {
            font-size: 16px;
            font-weight: 600;
            color: #f9fafb;
        }
        .header-sub {
            font-size: 11px;
            color: #9ca3af;
        }
        .label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #6b7280;
            margin-bottom: 4px;
        }
        .input {
            width: 100%;
            border-radius: 999px;
            border: 1px solid rgba(148, 163, 184, 0.35);
            background: rgba(15, 23, 42, 0.9);
            padding: 8px 12px;
            font-size: 13px;
            color: #e5e7eb;
            outline: none;
        }
        .input:focus {
            border-color: #4ade80;
            box-shadow: 0 0 0 1px rgba(74, 222, 128, 0.4);
        }
        .chat-box {
            height: 140px;
            border-radius: 12px;
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid rgba(31, 41, 55, 0.9);
            padding: 8px 10px;
            overflow-y: auto;
            font-size: 12px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .msg {
            padding: 4px 8px;
            border-radius: 8px;
            background: rgba(15, 118, 110, 0.2);
            border: 1px solid rgba(34, 197, 94, 0.25);
        }
        .msg-meta {
            font-size: 10px;
            color: #9ca3af;
            margin-bottom: 1px;
        }
        .msg-text {
            font-size: 12px;
            color: #e5e7eb;
        }
        .msg.me {
            align-self: flex-end;
            background: rgba(37, 99, 235, 0.2);
            border-color: rgba(59, 130, 246, 0.3);
        }
        .row {
            display: flex;
            gap: 8px;
            align-items: flex-end;
        }
        .textarea {
            flex: 1;
            min-height: 56px;
            max-height: 80px;
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.35);
            background: rgba(15, 23, 42, 0.9);
            padding: 8px 10px;
            font-size: 13px;
            color: #e5e7eb;
            resize: none;
            outline: none;
        }
        .textarea:focus {
            border-color: #4ade80;
            box-shadow: 0 0 0 1px rgba(74, 222, 128, 0.4);
        }
        .btn {
            border-radius: 999px;
            border: none;
            padding: 10px 16px;
            font-size: 13px;
            font-weight: 600;
            background: linear-gradient(135deg, #22c55e, #4ade80);
            color: #022c22;
            cursor: pointer;
            box-shadow:
                0 10px 30px rgba(34, 197, 94, 0.5),
                0 0 0 1px rgba(22, 163, 74, 0.6);
            white-space: nowrap;
        }
        .btn:active {
            transform: translateY(1px);
            box-shadow:
                0 5px 18px rgba(34, 197, 94, 0.55),
                0 0 0 1px rgba(22, 163, 74, 0.7);
        }
    </style>
</head>
<body>
<div class="card">
    <div>
        <div class="header-title">Mini Chat for Volodymyr &amp; Mari</div>
        <div class="header-sub">Локальний прототип поверх FastAPI + SQLite</div>
    </div>

    <div>
        <div class="label">Нік</div>
        <input id="sender" class="input" value="Vova" />
    </div>

    <div>
        <div class="label">Історія</div>
        <div id="chat" class="chat-box"></div>
    </div>

    <div class="label" style="margin-top: 6px;">
        Напиши повідомлення… (Enter = відправити, Shift+Enter = новий рядок)
    </div>
    <div class="row">
        <textarea id="message" class="textarea"></textarea>
        <button id="sendBtn" class="btn">Send</button>
    </div>
</div>

<script>
    const senderInput = document.getElementById("sender");
    const msgInput = document.getElementById("message");
    const chatBox = document.getElementById("chat");
    const sendBtn = document.getElementById("sendBtn");

    async function fetchMessages() {
        try {
            const res = await fetch("/messages?limit=50");
            const data = await res.json();
            renderMessages(data);
        } catch (e) {
            console.error("Failed to fetch messages", e);
        }
    }

    function renderMessages(list) {
        const me = senderInput.value.trim() || "Me";
        chatBox.innerHTML = "";
        for (const m of list) {
            const wrap = document.createElement("div");
            wrap.className = "msg" + (m.sender === me ? " me" : "");

            const meta = document.createElement("div");
            meta.className = "msg-meta";
            const t = new Date(m.timestamp);
            const timeStr = t.toLocaleTimeString("uk-UA", { hour: "2-digit", minute: "2-digit" });
            meta.textContent = `${m.sender} · ${timeStr}`;

            const text = document.createElement("div");
            text.className = "msg-text";
            text.textContent = m.text;

            wrap.appendChild(meta);
            wrap.appendChild(text);
            chatBox.appendChild(wrap);
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    async function sendMessage() {
        const sender = senderInput.value.trim();
        const text = msgInput.value.trim();
        if (!sender || !text) return;

        try {
            await fetch("/messages", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ sender, text }),
            });
            msgInput.value = "";
            await fetchMessages();
        } catch (e) {
            console.error("Failed to send message", e);
        }
    }

    sendBtn.addEventListener("click", sendMessage);
    msgInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    fetchMessages();
    setInterval(fetchMessages, 3000);
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def chat_page():
    return CHAT_HTML


# ---------- API-ендпоінти ----------

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/messages", response_model=List[MessageOut])
def get_messages(limit: int = 50):
    with Session(engine) as session:
        stmt = select(Message).order_by(Message.id.desc()).limit(limit)
        rows = list(session.exec(stmt))
        rows = list(reversed(rows))
        return [
            MessageOut(
                sender=row.sender,
                text=row.text,
                timestamp=row.timestamp.isoformat() + "Z",
            )
            for row in rows
        ]

@app.post("/messages", response_model=MessageOut)
def send_message(msg: MessageIn):
    now = datetime.utcnow()
    new_row = Message(sender=msg.sender, text=msg.text, timestamp=now)
    with Session(engine) as session:
        session.add(new_row)
        session.commit()
        session.refresh(new_row)

    return MessageOut(
        sender=new_row.sender,
        text=new_row.text,
        timestamp=new_row.timestamp.isoformat() + "Z",
    )