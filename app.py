from agents import researcher,research_team
from autogen_agentchat.messages import TextMessage

from typing import Any

from litestar import Litestar , post,get
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.openapi.config import OpenAPIConfig
from litestar.dto import DTOData
from litestar.di import Provide

from database import ResearchReport,db_plugin,provide_research_repo,ResearchReportRepo
from dto import ResearchReportDTO,ResearchReportCreateDTO

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


@post("/research",dto=ResearchReportCreateDTO,return_dto=ResearchReportDTO)
async def handle_research(data: DTOData[ResearchReport],reports_repo: ResearchReportRepo,db_session: AsyncSession) -> ResearchReport:

    topic_dict = data.as_builtins()
    topic_text = topic_dict.get("topic")
    response = await research_team.run(task=f"Research this: {topic_text}.")

    history: list[dict[str, Any]] = []
    final_text_summary = ""

    for m in response.messages:
        print(f"DEBUG: Source: {m.source}, Type: {type(m.content)}, Content: {m.content}")
        content_str = ""
        # Check if content is None (common during tool calls)
        if isinstance(m.content, str):
            content_str = m.content
        elif isinstance(m.content, list):
            content_str = " ".join([str(i) for i in m.content])

        if "TERMINATE" in content_str and m.source == "synthesizer":
            final_text_summary = content_str.replace("TERMINATE", "").strip()

        history.append({
            "role":m.source,
            "content":content_str.strip() or "[System Action]"
        })

        
    if not final_text_summary:
        final_text_summary = "Research completed. See raw logs for details."

    report_instance = data.create_instance(
        summary=final_text_summary,
        raw_logs={"history": history}
    )

    created_report = await reports_repo.add(report_instance)
    await db_session.commit()
    return created_report

@get("/research",return_dto=ResearchReportDTO)
async def list_research_reports(reports_repo: ResearchReportRepo) -> list[ResearchReport]:
    """Retrieves all research reports from the database."""
    return await reports_repo.list()

openapi_config = OpenAPIConfig(
    title="Litestar Example",
    description="Example of Litestar with Scalar OpenAPI docs",
    version="0.0.1",
    render_plugins=[ScalarRenderPlugin()],
)     

app = Litestar(
    route_handlers=[handle_research,list_research_reports],
    plugins=[db_plugin],
    debug=True,
    dependencies={"reports_repo":Provide(provide_research_repo)},
    openapi_config=openapi_config
               )

