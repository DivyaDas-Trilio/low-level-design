"""Application configuration — read from the ENVIRONMENT (12-Factor III).

The SAME immutable image reads these at runtime; only the environment differs
between dev / staging / prod (that is what makes "build once, deploy many" work).
Even business policy (the fine rate, the borrow limit) is config here — tunable
without a rebuild.

The DOMAIN never imports this module. Config is read at the edges — the
composition root (`main.py`) and the API assembly (`app.py`) — and the resulting
values are *injected* inward. Config stays a detail chosen at the boundary,
exactly like the repository implementation (Step 10's Dependency Inversion).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # `.env` is a LOCAL-DEV convenience only — it is git-ignored and never shipped.
    # In real environments the platform injects real environment variables.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- backing services (Factor IV: attached resources, swappable by URL) ---
    database_url: str = "sqlite:///./dev.db"     # prod sets DATABASE_URL (e.g. postgres://...)

    # --- observability ---
    log_level: str = "INFO"

    # --- business policy as config (still validated by the domain) ---
    fine_rate_paise: int = 500                   # ₹5/day late  (business rule #3)
    max_active_loans: int = 2                    # at most 2 copies at once (rule #4)

    # --- server (Factor VII: port binding) ---
    port: int = 8000
    workers: int = 4                             # gunicorn workers ≈ (2 × cores) + 1


settings = Settings()
