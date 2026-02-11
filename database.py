from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from litestar.plugins.sqlalchemy import (SQLAlchemyAsyncConfig,
                                         SQLAlchemyPlugin,
                                         base,
                                         AsyncSessionConfig,
                                         repository
                                         )
from typing import Any
from litestar.dto import dto_field
from sqlalchemy.ext.asyncio import AsyncSession



DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_db"


session_config =AsyncSessionConfig(expire_on_commit=False)
db_config = SQLAlchemyAsyncConfig(
    connection_string=DATABASE_URL,
    session_config=session_config,
    create_all=True
)
db_plugin = SQLAlchemyPlugin(config=db_config)

class ResearchReport(base.UUIDBase):

    topic: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text,default="",info=dto_field("read-only"))
    raw_logs: Mapped[dict[str,Any]] = mapped_column(JSONB,default=dict,info=dto_field("read-only"))

class ResearchReportRepo(repository.SQLAlchemyAsyncRepository[ResearchReport]):
    model_type = ResearchReport

async def provide_research_repo(db_session:AsyncSession) -> ResearchReportRepo:
    return ResearchReportRepo(session=db_session)