CREATE TABLE IF NOT EXISTS conversation (
    conversation_id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS turn (
    turn_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversation (conversation_id),
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS message (
    message_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversation (conversation_id),
    turn_id TEXT REFERENCES turn (turn_id),
    role TEXT NOT NULL,
    text TEXT NOT NULL
);

INSERT INTO conversation (conversation_id)
VALUES ('1')
ON CONFLICT (conversation_id) DO NOTHING;
