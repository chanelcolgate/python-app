from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "checks" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(32) NOT NULL,
    "type_check" VARCHAR(32) NOT NULL,
    "hop_ytv" INT   DEFAULT 0,
    "hop_vtg" INT   DEFAULT 0,
    "hop_jn" INT   DEFAULT 0,
    "loc_ytv" INT   DEFAULT 0,
    "loc_kids" INT   DEFAULT 0,
    "loc_jn" INT   DEFAULT 0,
    "lo_ytv" INT   DEFAULT 0,
    "lo_kids" INT   DEFAULT 0,
    "bom_gen" INT   DEFAULT 0,
    "bom_jun" INT   DEFAULT 0,
    "bom_vtgk" INT   DEFAULT 0,
    "bom_ytv" INT   DEFAULT 0,
    "bom_knp" INT   DEFAULT 0,
    "bom_sachet" INT   DEFAULT 0,
    "day_sachet" INT   DEFAULT 0,
    "pocky" INT   DEFAULT 0
);
COMMENT ON TABLE "checks" IS 'The Check model';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
