from datetime import datetime
from pathlib import Path
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


# ---------- Шлях до HTML-файлу ----------

BASE_DIR = Path(__file__).parent
CHAT_HTML_PATH = BASE_DIR / "templates" / "chat.html"


@app.get("/", response_class=HTMLResponse)
def chat_page():
    """
    Повертаємо HTML з окремого файлу templates/chat.html
    """
    html = CHAT_HTML_PATH.read_text(encoding="utf-8")
    return HTMLResponse(content=html)


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
