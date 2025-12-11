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

    # Нові поля для статусів
    delivered: bool = False
    read: bool = False
    reader: Optional[str] = None


@app.on_event("startup")
def on_startup():
    # ВАЖЛИВО: при зміні структури таблиці видаляй старий chat.db,
    # щоб створилась нова таблиця з потрібними колонками.
    SQLModel.metadata.create_all(engine)


# ---------- Pydantic-схеми для API ----------

class MessageIn(BaseModel):
    sender: str
    text: str


class MessageOut(BaseModel):
    id: int
    sender: str
    text: str
    timestamp: str
    delivered: bool
    read: bool


class MarkReadRequest(BaseModel):
    viewer: str


# ---------- HTML-чат ----------

CHAT_HTML = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8" />
    <title>Mini Chat</title>
    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
            background: #f5f7ff;
            color: #111827;
        }

        .card {
            width: min(900px, 100vw - 32px);
            height: min(640px, 100vh - 32px);
            border-radius: 28px;
            background: #ffffff;
            border: 2px solid #bfdbfe;
            box-shadow:
                0 20px 50px rgba(15, 23, 42, 0.15),
                0 0 0 1px rgba(148, 163, 184, 0.4);
            padding: 18px 20px 18px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .field-row {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #6b7280;
        }

        .input {
            width: 100%;
            border-radius: 999px;
            border: 1px solid #bfdbfe;
            background: #f9fbff;
            padding: 9px 14px;
            font-size: 14px;
            color: #111827;
            outline: none;
        }

        .input:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.4);
            background: #ffffff;
        }

        .chat-row {
            flex: 1;
            min-height: 0;          /* ключ, щоб flex-елемент реально міг рости */
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .chat-wrapper {
            flex: 1;
            min-height: 0;          /* дозволяє скролитися замість стиснення */
            border-radius: 20px;
            border: 1px solid #bfdbfe;
            background: #eff6ff;
            padding: 10px 10px 12px;
            overflow-y: auto;
            font-size: 13px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .msg-row {
            display: flex;
            width: 100%;
        }

        .msg-row.me {
            justify-content: flex-end;
        }

        .bubble {
            display: inline-block;
            max-width: 75%;
            padding: 6px 10px;
            border-radius: 14px;
            background: #dbeafe;
            border: 1px solid #93c5fd;
            color: #111827;
        }

        .bubble.me {
            background: #3b82f6;
            border-color: #1d4ed8;
            color: #eff6ff;
        }

        .msg-meta {
            font-size: 11px;
            opacity: 0.7;
            margin-bottom: 2px;
        }

        .msg-text {
            font-size: 13px;
            line-height: 1.25;
            white-space: pre-wrap;
            word-wrap: break-word;
        }

        .input-row {
            display: flex;
            gap: 10px;
            align-items: flex-end;
            margin-top: 4px;
        }

        .textarea {
            flex: 1;
            min-height: 56px;
            max-height: 110px;
            border-radius: 16px;
            border: 1px solid #bfdbfe;
            background: #f9fbff;
            padding: 10px 12px;
            font-size: 14px;
            color: #111827;
            resize: none;
            outline: none;
        }

        .textarea:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.4);
            background: #ffffff;
        }

        .btn {
            border-radius: 999px;
            border: none;
            padding: 11px 20px;
            font-size: 14px;
            font-weight: 600;
            background: linear-gradient(135deg, #3b82f6, #60a5fa);
            color: #f9fafb;
            cursor: pointer;
            box-shadow:
                0 12px 30px rgba(37, 99, 235, 0.5),
                0 0 0 1px rgba(30, 64, 175, 0.6);
            white-space: nowrap;
        }

        .btn:active {
            transform: translateY(1px);
            box-shadow:
                0 6px 16px rgba(37, 99, 235, 0.55),
                0 0 0 1px rgba(30, 64, 175, 0.7);
        }

        /* Мобільна версія */
        @media (max-width: 640px) {
            body {
                align-items: stretch;
                justify-content: flex-start;
            }

            .card {
                width: 100vw;
                height: 100vh;
                max-width: none;
                max-height: none;
                border-radius: 0;
                border-width: 1px;
                box-shadow: none;
                padding: 12px 12px 10px;
            }
        }
    </style>
</head>
<body>
<div class="card">
    <div class="field-row">
        <div class="label">Нік</div>
        <input id="sender" class="input" value="Vova" />
    </div>

    <div class="chat-row">
        <div class="label">Історія</div>
        <div id="chat" class="chat-wrapper"></div>
    </div>

    <div class="input-row">
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
            const row = document.createElement("div");
            row.className = "msg-row" + (m.sender === me ? " me" : "");

            const bubble = document.createElement("div");
            bubble.className = "bubble" + (m.sender === me ? " me" : "");

            const meta = document.createElement("div");
            meta.className = "msg-meta";
            const t = new Date(m.timestamp);
            const timeStr = t.toLocaleTimeString("uk-UA", { hour: "2-digit", minute: "2-digit" });
            meta.textContent = `${m.sender} · ${timeStr}`;

            const text = document.createElement("div");
            text.className = "msg-text";
            text.textContent = m.text;

            bubble.appendChild(meta);
            bubble.appendChild(text);
            row.appendChild(bubble);
            chatBox.appendChild(row);
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
def get_messages(limit: int = 50, viewer: Optional[str] = None):
    """
    Повертаємо останні повідомлення.
    Якщо переданий viewer, вважаємо всі повідомлення
    «доставленими» цьому користувачу.
    """
    with Session(engine) as session:
        # оновлюємо delivered, якщо користувач відкрив чат
        if viewer:
            stmt_to_deliver = select(Message).where(Message.delivered == False)
            for msg in session.exec(stmt_to_deliver):
                msg.delivered = True
            session.commit()

        stmt = select(Message).order_by(Message.id.desc()).limit(limit)
        rows = list(session.exec(stmt))
        rows = list(reversed(rows))

        return [
            MessageOut(
                id=row.id,
                sender=row.sender,
                text=row.text,
                timestamp=row.timestamp.isoformat() + "Z",
                delivered=row.delivered,
                read=row.read,
            )
            for row in rows
        ]


@app.post("/messages", response_model=MessageOut)
def send_message(msg: MessageIn):
    now = datetime.utcnow()
    new_row = Message(
        sender=msg.sender,
        text=msg.text,
        timestamp=now,
        delivered=False,
        read=False,
        reader=None,
    )
    with Session(engine) as session:
        session.add(new_row)
        session.commit()
        session.refresh(new_row)

    return MessageOut(
        id=new_row.id,
        sender=new_row.sender,
        text=new_row.text,
        timestamp=new_row.timestamp.isoformat() + "Z",
        delivered=new_row.delivered,
        read=new_row.read,
    )


@app.post("/messages/mark-read")
def mark_messages_read(payload: MarkReadRequest):
    """
    Позначаємо всі повідомлення, які НЕ від цього користувача,
    як прочитані ним.
    """
    viewer = payload.viewer.strip()
    if not viewer:
        return {"updated": 0}

    with Session(engine) as session:
        stmt = select(Message).where(
            Message.sender != viewer,
            Message.read == False
        )
        rows = list(session.exec(stmt))
        for row in rows:
            row.read = True
            row.delivered = True
            row.reader = viewer
        session.commit()

        return {"updated": len(rows)}
