import json
from typing import Any

from app.core.errors import ToolNotSupportedError
from app.core.settings import Settings
from app.tools import filesystem_tool, web_fetch, web_search


class ToolGateway:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def definitions(self) -> list[dict[str, Any]]:
        return [
            web_search.schema(),
            web_fetch.schema(),
            filesystem_tool.list_schema(),
            filesystem_tool.read_schema(),
        ]

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name == "web_search":
            return await web_search.execute(query=arguments["query"])

        if tool_name == "web_fetch":
            return await web_fetch.execute(url=arguments["url"])

        if tool_name == "list_workspace_files":
            return await filesystem_tool.list_workspace_files(
                workspace_root=self.settings.workspace_dir_abs,
                subpath=arguments.get("subpath", ""),
            )

        if tool_name == "read_workspace_file":
            return await filesystem_tool.read_workspace_file(
                workspace_root=self.settings.workspace_dir_abs,
                path=arguments["path"],
            )

        raise ToolNotSupportedError(f"Herramienta no soportada: {tool_name}")

    @staticmethod
    def normalize_arguments(raw_arguments: Any) -> dict[str, Any]:
        if isinstance(raw_arguments, dict):
            return raw_arguments
        if isinstance(raw_arguments, str):
            try:
                return json.loads(raw_arguments)
            except json.JSONDecodeError:
                return {}
        return {}
