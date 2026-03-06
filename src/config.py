from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Zendesk
    zendesk_subdomain: str = "teamleaderfocus"
    zendesk_api_email: str = ""
    zendesk_api_token: str = ""
    zendesk_webhook_secret: str = ""

    # OpenRouter (Gemini Flash)
    openrouter_api_key: str = ""

    # Focus Service
    focus_service_url: str = "http://api.ai-assistant.focus.teamleader.dev"

    # Server
    port: int = 8886
    log_level: str = "info"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
