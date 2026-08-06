import unittest

from config import load_settings, parse_cors_origins


BASE_ENV = {
    "ENVIRONMENT": "production",
    "CORS_ORIGINS": "https://app.example.com",
    "DB_SERVER": "sql.example.com",
    "DB_DATABASE": "RetroGarage",
    "DB_USER": "usuario",
    "DB_PASSWORD": "secreto",
    "DB_DRIVER": "ODBC Driver 18 for SQL Server",
}


class ConfigTests(unittest.TestCase):
    def test_cors_elimina_duplicados_y_barras_finales(self):
        origins = parse_cors_origins(
            "https://app.example.com/, https://app.example.com,http://localhost:8081/",
        )
        self.assertEqual(
            origins,
            ("https://app.example.com", "http://localhost:8081"),
        )

    def test_produccion_acepta_configuracion_completa(self):
        settings = load_settings(BASE_ENV)
        self.assertTrue(settings.production)
        self.assertEqual(settings.db_port, 1433)
        self.assertEqual(settings.db_encrypt, "yes")

    def test_produccion_rechaza_secretos_faltantes(self):
        incomplete = dict(BASE_ENV)
        incomplete.pop("DB_PASSWORD")
        with self.assertRaisesRegex(RuntimeError, "DB_PASSWORD"):
            load_settings(incomplete)

    def test_produccion_rechaza_cors_global(self):
        invalid = {**BASE_ENV, "CORS_ORIGINS": "*"}
        with self.assertRaisesRegex(RuntimeError, "no puede contener"):
            load_settings(invalid)


if __name__ == "__main__":
    unittest.main()
