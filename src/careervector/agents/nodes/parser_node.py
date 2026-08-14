from careervector.agents.state import CopilotState
from careervector.parsing.resume_parser import parse_resume


async def parser_node(state: CopilotState) -> CopilotState:
    candidate = await parse_resume(state["resume_text"], state["known_skills"], state["llm"])
    return CopilotState(candidate=candidate)
