from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from src.settings import Settings
from src.routes.check import check_router
from src.routes.image_display import image_display_router

settings = Settings()
app = FastAPI()

# Register routes
app.include_router(check_router, prefix="/check")
app.include_router(image_display_router, prefix="/image-display")


@app.get("/")
async def hello_world():
    return {"hello": "world"}


@app.on_event("startup")
async def startup():
    if settings.DEBUG:
        print(settings)


# psycopg://odoo:odoo@172.30.80.1:5432/vsk
TORTOISE_ORM = {
    "connections": {"default": settings.DATABASE_URL},
    "apps": {
        "models": {
            "models": ["src.models.check", "aerich.models"],
            "default_connection": "default",
        }
    },
}

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)
