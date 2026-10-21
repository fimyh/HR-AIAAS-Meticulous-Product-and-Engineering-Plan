from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from hr_aiaas.api.health import router as health_router
from hr_aiaas.config import get_settings
from hr_aiaas.graphql.context import get_context
from hr_aiaas.graphql.schema import schema

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Check folders, database, and required application resources here.
    yield
    # Close shared resources here.


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
)

graphql_router = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphql_ide="graphiql" if settings.app_env == "development" else None,
)

app.include_router(graphql_router, prefix="/graphql")
app.include_router(health_router)