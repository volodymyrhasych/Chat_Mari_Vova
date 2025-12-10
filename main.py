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


# ---------- HTML-чат (світла тема) ----------

CHAT_HTML = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8" />
    <title>Mini Chat</title>
    <style>
        body {
            margin: 0;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
            background: #f5f7ff;
            color: #111827;
        }

        .card {
            width: min(720px, 100vw - 32px);
            height: min(640px, 100vh - 32px);
            background: #ffffff;
            border-radius: 28px;
            border: 2px solid #9bbcff;
            box-shadow:
                0 18px 40px rgba(15, 23, 42, 0.15),
                0 0 0 1px rgba(148, 163, 184, 0.18);
            padding: 20px 22px 18px;
            display: flex;
            flex-direction: column;
            gap: 12px;
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
            border: 1px solid #bfccff;
            background: #f6f7ff;
            padding: 8px 12px;
            font-size: 13px;
            color: #111827;
            outline: none;
        }
        .input:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.35);
            background: #ffffff;
        }

        .chat-wrapper {
            flex: 1;
            min-height: 0;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .chat-box {
            flex: 1;
            border-radius: 16px;
            background: #f3f6ff;
            border: 1px solid #c7d2fe;
            padding: 10px 12px;
            overflow-y: auto;
            font-size: 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .msg {
            display: inline-block;
            max-width: 75%;
            padding: 6px 9px;
            border-radius: 14px;
            background: #e5edff;
            border: 1px solid #bfccff;
            align-self: flex-start;
        }

        .msg.me {
            align-self: flex-end;
            background: #dbeafe;
            border-color: #93c5fd;
        }

        .msg-meta {
            font-size: 10px;
            color: #6b7280;
            margin-bottom: 2px;
        }

        .msg-text {
            font-size: 12px;
            color: #111827;
            word-wrap: break-word;
            white-space: pre-wrap;
        }

        .row {
            display: flex;
            gap: 8px;
            align-items: flex-end;
            margin-top: 4px;
        }

        .textarea {
            flex: 1;
            min-height: 64px;
            max-height: 100px;
            border-radius: 16px;
            border: 1px solid #bfccff;
            background: #f6f7ff;
            padding: 8px 11px;
            font-size: 13px;
            color: #111827;
            resize: none;
            outline: none;
        }
        .textarea:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.35);
            background: #ffffff;
        }

        .btn {
            border-radius: 999px;
            border: none;
            padding: 10px 20px;
            font-size: 13px;
            font-weight: 600;
            background: linear-gradient(135deg, #2563eb, #60a5fa);
            color: #eff6ff;
            cursor: pointer;
            box-shadow:
                0 12px 26px rgba(37, 99, 235, 0.45),
                0 0 0 1px rgba(37, 99, 235, 0.7);
            white-space: nowrap;
        }
        .btn:active {
            transform: translateY(1px);
            box-shadow:
                0 6px 16px rgba(37, 99, 235, 0.5),
                0 0 0 1px rgba(37, 99, 235, 0.8);
        }
    </style>
</head>
<body>
<div class="card">
    <div>
        <div class="label">Нік</div>
        <input id="sender" class="input" value="Vova" />
    </div>

    <div class="chat-wrapper">
        <div class="label">Історія</div>
        <div id="chat" class="chat-box"></div>
    </div>

    <div class="row">
        <textarea id="message" class="textarea" placeholder="Напиши повідомлення…"></textarea>
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
