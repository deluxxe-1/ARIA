from app.core.router import TaskRouter


def test_decide_code_route_by_keyword() -> None:
    router = TaskRouter()
    decision = router.decide("Crea un script en Python que calcule fibonacci")
    assert decision.route == "code"


def test_decide_research_route_by_keyword() -> None:
    router = TaskRouter()
    decision = router.decide("Busca noticias recientes y documentacion actual sobre modelos de lenguaje")
    assert decision.route == "research"


def test_decide_general_route_default() -> None:
    router = TaskRouter()
    decision = router.decide("Hola ARIA, que tal estas hoy?")
    assert decision.route == "general"
