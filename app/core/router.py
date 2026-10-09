from dataclasses import dataclass

CODE_KEYWORDS = {
    "codigo",
    "programa",
    "programar",
    "web",
    "pagina",
    "aplicacion",
    "api",
    "backend",
    "frontend",
    "react",
    "next",
    "fastapi",
    "bug",
    "error",
    "refactor",
    "script",
}

RESEARCH_KEYWORDS = {
    "busca",
    "buscar",
    "internet",
    "web search",
    "investiga",
    "documentacion",
    "ultima version",
    "ultimas noticias",
}


@dataclass
class RouterDecision:
    route: str
    reason: str


class TaskRouter:
    def decide(self, prompt: str) -> RouterDecision:
        text = prompt.lower()

        if any(word in text for word in CODE_KEYWORDS):
            return RouterDecision(route="code", reason="detectado lenguaje de desarrollo")

        if any(word in text for word in RESEARCH_KEYWORDS):
            return RouterDecision(route="research", reason="detectada necesidad de datos externos")

        return RouterDecision(route="general", reason="consulta general")
