import json
from uuid import uuid4

from app.core.abstractions import ChatMemory, LLMProvider
from app.core.router import TaskRouter
from app.core.settings import Settings
from app.core.tool_gateway import ToolGateway
from app.models.coder_llm import CoderLLM
from app.models.planner_llm import PlannerLLM
from app.schemas.chat import ChatRequest, ChatResponse, ToolExecution


class Orchestrator:
    def __init__(
        self,
        settings: Settings,
        memory: ChatMemory,
        router: TaskRouter,
        planner: PlannerLLM,
        coder: CoderLLM,
        tool_gateway: ToolGateway,
    ) -> None:
        self.settings = settings
        self.memory: ChatMemory = memory
        self.router = router
        self.planner: LLMProvider | PlannerLLM = planner
        self.coder = coder
        self.tool_gateway = tool_gateway

    async def handle_chat(self, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or uuid4().hex
        history = await self.memory.get_recent_messages(session_id=session_id)
        decision = self.router.decide(request.prompt)

        await self.memory.save_message(
            session_id=session_id,
            role="user",
            content=request.prompt,
            route=decision.route,
        )

        if decision.route == "code":
            plan = await self.planner.plan_for_code(history=history, prompt=request.prompt)
            coder_answer = await self.coder.generate(
                history=history,
                prompt=request.prompt,
                plan=plan,
            )
            answer = f"Plan de ARIA:\n{plan}\n\nRespuesta tecnica:\n{coder_answer}".strip()
            model_used = self.settings.coder_model
            tool_runs: list[ToolExecution] = []
        else:
            answer, tool_runs = await self._run_planner_with_tools(
                history=history,
                prompt=request.prompt,
                allow_tools=request.allow_tools,
            )
            model_used = self.settings.planner_model

        await self.memory.save_message(
            session_id=session_id,
            role="assistant",
            content=answer,
            model=model_used,
            route=decision.route,
        )

        return ChatResponse(
            answer=answer,
            session_id=session_id,
            route=decision.route,
            model_used=model_used,
            tool_runs=tool_runs,
        )

    async def _run_planner_with_tools(
        self,
        history: list[dict[str, str]],
        prompt: str,
        allow_tools: bool,
    ) -> tuple[str, list[ToolExecution]]:
        messages = self.planner.build_messages(history=history, prompt=prompt)
        tools = self.tool_gateway.definitions() if allow_tools else None
        tool_runs: list[ToolExecution] = []

        for _ in range(self.settings.max_tool_iterations):
            response = await self.planner.client.chat(
                model=self.settings.planner_model,
                messages=messages,
                tools=tools,
            )
            message = response.get("message", {})
            tool_calls = message.get("tool_calls") or []

            if not tool_calls:
                return message.get("content", "").strip(), tool_runs

            messages.append(message)

            for call in tool_calls:
                function_data = call.get("function", {})
                tool_name = function_data.get("name", "")
                arguments = self.tool_gateway.normalize_arguments(function_data.get("arguments", {}))
                result = await self.tool_gateway.execute(tool_name=tool_name, arguments=arguments)
                preview = json.dumps(result, ensure_ascii=False)[:300]

                tool_runs.append(
                    ToolExecution(
                        name=tool_name,
                        arguments=arguments,
                        result_preview=preview,
                    )
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_name": tool_name,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        return (
            "He alcanzado el limite de iteraciones de herramientas para esta peticion.",
            tool_runs,
        )
