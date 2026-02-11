from litestar.plugins.sqlalchemy import SQLAlchemyDTO,SQLAlchemyDTOConfig
from litestar.dto import dto_field,DTOConfig
from database import ResearchReport

class ResearchReportDTO(SQLAlchemyDTO[ResearchReport]):
    config = DTOConfig()

class ResearchReportCreateDTO(SQLAlchemyDTO[ResearchReport]):
    config = DTOConfig(exclude={"id","summary","raw_logs"})