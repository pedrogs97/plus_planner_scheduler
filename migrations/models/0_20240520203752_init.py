from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "holidays" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "deleted" BOOL NOT NULL  DEFAULT False,
    "date" TIMESTAMPTZ NOT NULL,
    "name" VARCHAR(100) NOT NULL,
    "type" VARCHAR(100) NOT NULL,
    "level" VARCHAR(100) NOT NULL
);
COMMENT ON TABLE "holidays" IS 'Model to represent a holiday.';
CREATE TABLE IF NOT EXISTS "schedulers" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "deleted" BOOL NOT NULL  DEFAULT False,
    "status" VARCHAR(20) NOT NULL  DEFAULT 'WAITING_CONFIRMATION',
    "date" TIMESTAMPTZ NOT NULL,
    "description" TEXT,
    "is_return" BOOL NOT NULL  DEFAULT False,
    "is_off" BOOL NOT NULL  DEFAULT False,
    "off_reason" TEXT,
    "clinic_id" BIGINT NOT NULL,
    "patient" VARCHAR(150) NOT NULL,
    "user" VARCHAR(150) NOT NULL,
    "desk" VARCHAR(150) NOT NULL
);
COMMENT ON COLUMN "schedulers"."status" IS 'WAITING_CONFIRMATION: WAITING_CONFIRMATION\nCONFIRMED: CONFIRMED\nCANCELED: CANCELED\nDONE: DONE';
COMMENT ON TABLE "schedulers" IS 'Model to represent a scheduler.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
