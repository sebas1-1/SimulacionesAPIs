import pyodbc

from config import settings


def _proteger_valor_odbc(value: str) -> str:
    return "{" + value.replace("}", "}}") + "}"


def obtener_conexion():
    connection_string = (
        f"DRIVER={{{settings.db_driver}}};"
        f"SERVER=tcp:{settings.db_server},{settings.db_port};"
        f"DATABASE={_proteger_valor_odbc(settings.db_database)};"
        f"UID={_proteger_valor_odbc(settings.db_user)};"
        f"PWD={_proteger_valor_odbc(settings.db_password)};"
        f"Encrypt={settings.db_encrypt};"
        f"TrustServerCertificate={settings.db_trust_server_certificate};"
        f"Connection Timeout={settings.db_connection_timeout_seconds};"
    )

    return pyodbc.connect(
        connection_string,
        timeout=settings.db_connection_timeout_seconds,
    )
