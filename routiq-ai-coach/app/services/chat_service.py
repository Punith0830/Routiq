"""Live service injection is explicit. No secret loading on application import."""
from app.ai.agents.habit_coach import openai_generate


class CoachUnavailable(RuntimeError):
    def __init__(self, code="COACH_UNAVAILABLE", message="The coach could not reply safely. Check your API settings or connection and try again."):
        super().__init__(message)
        self.code = code


def safe_provider_error(error):
    from openai import APIConnectionError, APITimeoutError
    from pydantic import ValidationError
    from app.ai.guardrails import UnsafeCoachOutput
    if isinstance(error, UnsafeCoachOutput):
        return CoachUnavailable("COACH_RESPONSE_REJECTED", "The reply was blocked because it included unverified claims or did not pass response checks. No habit data is connected. Try asking for a brief general habit suggestion without numbers.")
    if isinstance(error, ValidationError):
        return CoachUnavailable("COACH_OUTPUT_FORMAT", "OpenAI returned an empty or invalid structured reply. Check that the model supports structured output, then try a shorter question.")
    status = getattr(error, "status_code", None)
    if status == 401:
        return CoachUnavailable("OPENAI_AUTH_FAILED", "OpenAI rejected the API key. Replace it with a valid new key, save .env and enable /live again.")
    if status == 429:
        if getattr(error, "code", None) == "insufficient_quota":
            return CoachUnavailable("OPENAI_QUOTA", "OpenAI reports insufficient API quota. Check your API project billing and credits.")
        return CoachUnavailable("OPENAI_RATE_LIMIT", "OpenAI rate-limited the request. Wait briefly before trying again; check API quota if it persists.")
    if status in {403, 404}:
        return CoachUnavailable("OPENAI_MODEL_ACCESS", "OpenAI denied access to the configured model or could not find it. Check OPENAI_MODEL and your API project permissions.")
    if isinstance(error, APITimeoutError):
        return CoachUnavailable("OPENAI_TIMEOUT", "OpenAI did not respond within the request timeout. Try again later.")
    if isinstance(error, APIConnectionError):
        return CoachUnavailable("OPENAI_CONNECTION", "Could not connect to OpenAI. Check your internet connection, proxy or firewall.")
    if status == 400:
        return CoachUnavailable("OPENAI_REQUEST_REJECTED", "OpenAI rejected the request format. Check that your model supports Responses and structured output.")
    if status and status >= 500:
        return CoachUnavailable("OPENAI_SERVICE_ERROR", "OpenAI returned a service error. Try again later.")
    return CoachUnavailable("COACH_PROVIDER_FAILURE", "The provider adapter failed before a valid reply was available. This is an unclassified local/provider failure, not evidence of an invalid API key.")


class LiveCoachService:
    def __init__(self, settings, generate=None):
        self.settings = settings
        self.generate = generate or openai_generate

    def respond(self, request, config):
        from app.ai.flow import run_flow
        failure = None

        def guarded_generate(settings, message):
            nonlocal failure
            try:
                from app.ai.guardrails import validate_message
                return validate_message(self.generate(settings, message), settings.api_key.get_secret_value())
            except Exception as error:
                failure = safe_provider_error(error)
                raise RuntimeError("Coach generation unavailable") from None

        try:
            return run_flow(request, config, self.settings, guarded_generate)
        except Exception:
            # Neither exception repr nor provider error bodies are returned/logged.
            raise (failure or CoachUnavailable("COACH_EXECUTION_FAILED", "The local CrewAI flow failed. Restart the notebook kernel to reload the latest modules; if it persists, report this error code.")) from None
