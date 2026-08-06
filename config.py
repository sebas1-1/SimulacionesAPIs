import os
from dataclasses import dataclass
from typing import Mapping

from dotenv import load_dotenv


load_dotenv()


LOCAL_ORIGINS = (
    "http://localhost:8081",
    "http://127.0.0.1:8081",
)


def parse_cors_origins(value: str | None, production: bool = False) -> tuple[str, ...]:
    if not value:
        return () if production else LOCAL_ORIGINS

    origins: list[str] = []
    for item in value.split(","):
        origin = item.strip().rstrip("/")
        if origin and origin not in origins:
            origins.append(origin)
    return tuple(origins)


def parse_positive_integer(value: str | None, default: int) -> int:
    try:
        parsed = int(value or "")
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def parse_yes_no(value: str | None, default: str) -> str:
    if value is None or not value.strip():
        return default
    normalized = value.strip().lower()
    if normalized in {"yes", "true"}:
        return "yes"
    if normalized in {"no", "false"}:
        return "no"
    raise RuntimeError("DB_ENCRYPT y DB_TRUST_SERVER_CERTIFICATE deben ser yes/no o true/false")


@dataclass(frozen=True)
class Settings:
    environment: str
    cors_origins: tuple[str, ...]
    db_server: str
    db_database: str
    db_user: str
    db_password: str
    db_port: int
    db_driver: str
    db_encrypt: str
    db_trust_server_certificate: str
    db_connection_timeout_seconds: int

    @property
    def production(self) -> bool:
        return self.environment == "production"


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    env = os.environ if environ is None else environ
    environment = env.get("ENVIRONMENT", "development").strip().lower()
    production = environment == "production"

    required = ("DB_SERVER", "DB_DATABASE", "DB_USER", "DB_PASSWORD", "DB_DRIVER")
    if production:
        required += ("CORS_ORIGINS",)

    missing = [name for name in required if not env.get(name, "").strip()]
    if missing:
        raise RuntimeError(f"Faltan variables obligatorias: {', '.join(missing)}")

    cors_origins = parse_cors_origins(env.get("CORS_ORIGINS"), production)
    if production and "*" in cors_origins:
        raise RuntimeError("CORS_ORIGINS no puede contener * en producción")

    for origin in cors_origins:
        if not origin.startswith(("http://", "https://")):
            raise RuntimeError(f"Origen CORS inválido: {origin}")

    return Settings(
        environment=environment,
        cors_origins=cors_origins,
        db_server=env.get("DB_SERVER", "").strip(),
        db_database=env.get("DB_DATABASE", "").strip(),
        db_user=env.get("DB_USER", "").strip(),
        db_password=env.get("DB_PASSWORD", ""),
        db_port=parse_positive_integer(env.get("DB_PORT"), 1433),
        db_driver=env.get("DB_DRIVER", "").strip(),
        db_encrypt=parse_yes_no(env.get("DB_ENCRYPT"), "yes" if production else "no"),
        db_trust_server_certificate=parse_yes_no(
            env.get("DB_TRUST_SERVER_CERTIFICATE"),
            "yes",
        ),
        db_connection_timeout_seconds=parse_positive_integer(
            env.get("DB_CONNECTION_TIMEOUT_SECONDS"),
            10,
        ),
    )


settings = load_settings()
