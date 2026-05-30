-- Consent records for agentic authorization (DB-029)
CREATE TABLE IF NOT EXISTS consent_records (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    service TEXT NOT NULL,
    scope JSONB NOT NULL DEFAULT '[]',
    agent_id TEXT NOT NULL DEFAULT 'calendar',
    consent_type TEXT NOT NULL CHECK (consent_type IN ('session', 'time_bounded', 'recurring')),
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    times_used INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    revocation_reason TEXT,
    UNIQUE (user_id, service)
);

CREATE INDEX IF NOT EXISTS idx_consent_records_user_id ON consent_records (user_id);
CREATE INDEX IF NOT EXISTS idx_consent_records_expires_at ON consent_records (expires_at);

CREATE TABLE IF NOT EXISTS consent_audit_log (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    consent_id UUID REFERENCES consent_records (id),
    action TEXT NOT NULL,
    service TEXT NOT NULL DEFAULT '',
    details TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_consent_audit_user_id ON consent_audit_log (user_id);

-- User preferences (DB-034)
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    preference_text TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    source_briefing_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences (user_id);
