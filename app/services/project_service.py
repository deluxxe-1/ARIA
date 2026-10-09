import json

from app.core.settings import Settings
from app.schemas.projects import ProjectCreateRequest, ProjectCreateResponse
from slugify import slugify


class ProjectService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.settings.workspace_dir_abs.mkdir(parents=True, exist_ok=True)

    def create_project(self, payload: ProjectCreateRequest) -> ProjectCreateResponse:
        project_id = slugify(payload.name)
        project_dir = self.settings.workspace_dir_abs / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        readme_path = project_dir / "README.md"
        metadata_path = project_dir / "project.json"

        readme_path.write_text(
            "\n".join(
                [
                    f"# {payload.name}",
                    "",
                    payload.description,
                    "",
                    f"- Stack sugerido: `{payload.stack}`",
                    "- Creado por ARIA",
                ]
            ),
            encoding="utf-8",
        )
        metadata_path.write_text(
            json.dumps(payload.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return ProjectCreateResponse(
            project_id=project_id,
            name=payload.name,
            path=str(project_dir),
            readme_path=str(readme_path),
            message="Proyecto creado correctamente en el workspace.",
        )
