-- User table DDL and login-ready seed data
BEGIN;

CREATE TABLE IF NOT EXISTS "User" (
    "userId"      BIGSERIAL PRIMARY KEY,
    "anonymousId" UUID UNIQUE,
    "name"        TEXT,
    "email"       TEXT,
    "passwordHash" TEXT,
    "createdAt"   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "upadateAt"   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO "User" (
    "anonymousId", "name", "email", "passwordHash", "createdAt", "upadateAt"
) VALUES
('11111111-1111-1111-1111-111111111111', 'Test Taro',  'taro@example.com',   'Password123!', NOW(), NOW()),
('22222222-2222-2222-2222-222222222222', 'Test User2', 'hanako@example.com', 'SecretPwd#2', NOW(), NOW()),
('33333333-3333-3333-3333-333333333333', 'Dev Admin',  'admin@example.com',  'AdminPass!3', NOW(), NOW());

COMMIT;
