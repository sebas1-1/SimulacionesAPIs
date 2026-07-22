import os

import pyodbc
from dotenv import load_dotenv


load_dotenv()


def obtener_conexion():
    servidor = os.getenv("DB_SERVER")
    base_datos = os.getenv("DB_DATABASE")
    usuario = os.getenv("DB_USER")
    contrasena = os.getenv("DB_PASSWORD")
    puerto = os.getenv("DB_PORT")
    controlador = os.getenv("DB_DRIVER")

    connection_string = (
        f"DRIVER={{{controlador}}};"
        f"SERVER={servidor},{puerto};"
        f"DATABASE={base_datos};"
        f"UID={usuario};"
        f"PWD={contrasena};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(connection_string, timeout=5)