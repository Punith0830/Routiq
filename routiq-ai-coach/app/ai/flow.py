"""CrewAI Flow: controlled routing -> selective generation -> validation."""
import json

from app.ai.agents.habit_coach import make_agent
from app.ai.guardrails import classify, validate_message
from app.ai.runtime import prepare_runtime
from app.schemas.chat import ChatResponse


def run_flow(request, config, settings, generate):
    prepare_runtime(settings.project_root)
    from crewai.flow.flow import Flow, listen, start
    from crewai.events.utils.console_formatter import set_suppress_console_output
    set_suppress_console_output(True)

    class CoachFlow(Flow):
        @start()
        def resolve_scope(self):
            return classify(request, config)

        @listen(resolve_scope)
        async def generate_reply(self, route):
            if route.message is not None:
                return route, route.message
            agent = make_agent(settings, route.supported_message, generate)
            result = await agent.kickoff_async("Answer this general habit question without tools.")
            message = json.loads(result.raw)["message"]
            return route, validate_message(message, settings.api_key.get_secret_value())

        @listen(generate_reply)
        def format_reply(self, result):
            route, message = result
            if route.limitation:
                message += " " + route.limitation
            return ChatResponse(conversation_id=None, intents=[route.intent], message=message,
                                limitations=["Habit data and saved conversation memory are not connected."])

    return CoachFlow(tracing=False, suppress_flow_events=True).kickoff()
