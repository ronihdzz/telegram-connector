from core.settings.base import Settings
from core.settings.base import ProjectSettings
from pydantic import Field

class TestingSettings(Settings):
    PROJECT: ProjectSettings = Field(
        default=ProjectSettings(
            NAME="Books API",
            DESCRIPTION="API implemented with FastAPI",
            VERSION="1.0.0",
            CODE="api-001",
            AUTHORS="R2"
        ),
        validate_default=True
    )