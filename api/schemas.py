from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

AccessStatus = Literal["pending", "allowed", "blocked"]
AccessMode = Literal["open", "allowlist"]


class User(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str
    last_name: str | None = None
    language_code: str | None = None
    is_premium: bool = False
    first_seen_at: datetime
    last_seen_at: datetime
    access_status: AccessStatus
    access_note: str | None = None
    access_updated_at: datetime | None = None


class UserPage(BaseModel):
    items: list[User]
    total: int
    limit: int
    offset: int


class AccessUpdate(BaseModel):
    status: AccessStatus
    note: str | None = None


class AccessGrant(BaseModel):
    """Pre-authorize (or pre-block) a Telegram id that has never messaged the bot."""

    telegram_id: int
    status: AccessStatus = "allowed"
    username: str | None = None
    first_name: str = Field(default="(pre-authorized)")
    note: str | None = None


class AccessSettings(BaseModel):
    access_mode: AccessMode
    access_denied_message: str


class AccessSettingsUpdate(BaseModel):
    access_mode: AccessMode | None = None
    access_denied_message: str | None = None


class AccessOverview(BaseModel):
    settings: AccessSettings
    users: dict[str, int]


class BotSettings(BaseModel):
    enabled: bool
    access_mode: AccessMode
    access_denied_message: str


class BotSettingsUpdate(BaseModel):
    enabled: bool | None = None
    access_mode: AccessMode | None = None
    access_denied_message: str | None = None


class BotIdentity(BaseModel):
    id: int
    username: str | None = None
    first_name: str | None = None
    reachable: bool
    error: str | None = None


class BotStatus(BaseModel):
    settings: BotSettings
    identity: BotIdentity
    users: dict[str, int]
    messages: dict[str, int]


class LoggedMessage(BaseModel):
    id: int
    direction: Literal["in", "out"]
    chat_id: int | None = None
    user_id: int | None = None
    event_type: str
    text: str | None = None
    telegram_message_id: int | None = None
    created_at: datetime


class MessagePage(BaseModel):
    items: list[LoggedMessage]
    limit: int
    offset: int


class SendMessageRequest(BaseModel):
    chat_id: int
    text: str = Field(min_length=1, max_length=4096)
    # Bypass the access check — for support replies to a user who is not allowed in.
    force: bool = False


class SendMessageResponse(BaseModel):
    telegram_message_id: int
    chat_id: int
    sent_at: datetime
