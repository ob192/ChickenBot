export type AccessStatus = "pending" | "allowed" | "blocked";
export type AccessMode = "open" | "allowlist";

export interface User {
  telegram_id: number;
  username: string | null;
  first_name: string;
  last_name: string | null;
  language_code: string | null;
  is_premium: boolean;
  first_seen_at: string;
  last_seen_at: string;
  access_status: AccessStatus;
  access_note: string | null;
  access_updated_at: string | null;
}

export interface UserPage {
  items: User[];
  total: number;
  limit: number;
  offset: number;
}

export interface LoggedMessage {
  id: number;
  direction: "in" | "out";
  chat_id: number | null;
  user_id: number | null;
  event_type: string;
  text: string | null;
  telegram_message_id: number | null;
  created_at: string;
}

export interface MessagePage {
  items: LoggedMessage[];
  limit: number;
  offset: number;
}

export interface BotSettings {
  enabled: boolean;
  access_mode: AccessMode;
  access_denied_message: string;
}

export interface BotStatus {
  settings: BotSettings;
  identity: {
    id: number;
    username: string | null;
    first_name: string | null;
    reachable: boolean;
    error: string | null;
  };
  users: Record<string, number>;
  messages: Record<string, number>;
}
