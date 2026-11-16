"""Tests automatizados para la redacción de datos sensibles en MS2.

Cubre la función is_sensitive_key() y redact_value() del módulo
src.core.logging_config, según la especificación del Factor 11
(12-Factor App logging).
"""

from src.core.logging_config import is_sensitive_key, redact_value


class TestIsSensitiveKey:
    """Tests para la función is_sensitive_key().

    Esta función determina si una clave debe tratarse como sensible
    basándose en nombre de clave normalizado y coincidencia con
    SENSITIVE_KEYS / SENSITIVE_KEY_TOKENS.
    """

    # Claves sensibles literales que deben reconocerse
    SENSITIVE_LITERALS = [
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "api_key",
        "authorization",
        "cookie",
        "credential",
        "private_key",
    ]

    # Variantes con diferentes mayúsculas/minúsculas y separadores
    SENSITIVE_VARIANTS = [
        # Mayúsculas completas
        "PASSWORD",
        "SECRET",
        "TOKEN",
        "API_KEY",
        "AUTHORIZATION",
        "COOKIE",
        "CREDENTIAL",
        "PRIVATE_KEY",
        # CamelCase
        "Password",
        "Secret",
        "Token",
        "ApiKey",
        "Authorization",
        "Cookie",
        "Credential",
        "PrivateKey",
        # Con guiones
        "api-key",
        "access-token",
        "private-key",
        # Con prefijos/sufijos habituales
        "db_password",
        "api_key_v2",
        "access_token",
        "refresh_token",
        "set-cookie",
        "proxy-authorization",
    ]

    # Claves que NO deben considerarse sensibles
    INSENSITIVE_KEYS = [
        "endpoint",
        "request_id",
        "trace_id",
        "span_id",
        "message",
        "level",
        "service",
        "logger",
        "timestamp",
        "custom_param",
        "output_format",
        "page_number",
    ]

    def test_literal_sensitive_keys(self):
        """Test 1-10: Claves sensibles literales deben reconocerse."""
        for key in self.SENSITIVE_LITERALS:
            result = is_sensitive_key(key)
            assert result is True, f"Expected '{key}' to be sensitive, got {result}"

    def test_sensitive_variants_with_case(self):
        """Test 11-18: Variantes con mayúsculas/minúsculas deben reconocerse."""
        for key in self.SENSITIVE_VARIANTS:
            result = is_sensitive_key(key)
            assert result is True, f"Expected '{key}' to be sensitive, got {result}"

    def test_insensitive_keys_rejected(self):
        """Test 19: Claves no sensibles deben rechazarse."""
        for key in self.INSENSITIVE_KEYS:
            result = is_sensitive_key(key)
            assert result is False, f"Expected '{key}' to be insensitive, got {result}"

    def test_variants_with_underscores(self):
        """Test 20-21: Variantes con guión bajo deben reconocerse."""
        # access_token y api_key ya están en SENSITIVE_LITERALS,
        # pero probamos específicamente la variante con underscore
        assert is_sensitive_key("access_token") is True
        assert is_sensitive_key("api_key") is True

    def test_variants_with_hyphens(self):
        """Test 22-24: Variantes con guión deben reconocerse."""
        assert is_sensitive_key("api-key") is True
        assert is_sensitive_key("access-token") is True
        assert is_sensitive_key("private-key") is True

    def test_suffixes_and_prefixes(self):
        """Test 25-30: Prefijos y sufijos habituales deben reconocerse."""
        for key in [
            "db_password",
            "api_key_v2",
            "access_token",
            "refresh_token",
            "set-cookie",
            "proxy-authorization",
        ]:
            assert is_sensitive_key(key) is True, f"Expected '{key}' to be sensitive"


class TestRedactValue:
    """Tests para la función redact_value().

    Esta función reemplaza valores asociados a claves sensibles
    por "***" y conserva valores de claves no sensibles.
    """

    def test_sensitive_key_redacted(self):
        """Test 31: Valor asociado a clave sensible debe ser ***."""
        # password
        result = redact_value("password", "my_secret_pass")
        assert result == "***", f"Expected '***', got {result}"

        # token
        result = redact_value("token", "abc123xyz")
        assert result == "***", f"Expected '***', got {result}"

        # api_key
        result = redact_value("api_key", "sk-1234567890abcdef")
        assert result == "***", f"Expected '***', got {result}"

        # secret
        result = redact_value("secret", "highly_classified")
        assert result == "***", f"Expected '***', got {result}"

    def test_insensitive_key_not_redacted(self):
        """Test 32: Valor asociado a clave no sensible debe conservarse."""
        # endpoint
        result = redact_value("endpoint", "/api/v1/users")
        assert result == "/api/v1/users", f"Expected '/api/v1/users', got {result}"

        # request_id
        result = redact_value("request_id", "req-998877")
        assert result == "req-998877", f"Expected 'req-998877', got {result}"

        # message (no es una clave de contexto típica, pero probamos)
        result = redact_value("message", "Operación completada")
        assert result == "Operación completada", f"Expected 'Operación completada', got {result}"

    def test_redact_mixed_keys(self):
        """Test 33: Diccionario mixto de claves sensibles y no sensibles."""
        mapping = {
            "url": "mongodb://host:27017",
            "password": "secret123",
            "endpoint": "/health",
            "api_key": "sk-test",
        }
        result = redact_value("", mapping)
        # password y api_key deben ser redactadas
        assert result["password"] == "***", f"Expected password to be redacted, got {result['password']}"
        assert result["api_key"] == "***", f"Expected api_key to be redacted, got {result['api_key']}"
        # url y endpoint deben conservarse
        assert result["url"] == "mongodb://host:27017", f"Expected url unchanged, got {result['url']}"
        assert result["endpoint"] == "/health", f"Expected endpoint unchanged, got {result['endpoint']}"

    def test_redact_value_sensitive_key_immediate_redact(self):
        """Test 34: Clave sensible retorna *** inmediatamente, sin recursar.

        El comportamiento actual de redact_value() es devolver "***"
        de inmediato cuando la clave es sensible, sin inspeccionar el
        valor/estructura del mismo.
        """
        result = redact_value("password", {"db_password": "internal", "host": "localhost"})
        assert result == "***", f"Expected '***', got {result}"

    def test_redact_value_with_list(self):
        """Test 35: Lista de valores con una clave sensible.

        Cuando redact_value recibe una lista (o tupla/set/frozenset), itera
        sobre cada elemento aplicando la lógica de redacción recursiva. Dado
        que los elementos son strings puros y no hay una clave asociada por nombre
        (key="" vacío), los strings se conservan tal cual (no hay clave sensible
        que activar la redacción sobre el string en sí mismo).
        """
        result = redact_value("", ["public_item", "secret_value"])
        assert result == ["public_item", "secret_value"], f"Expected ['public_item', 'secret_value'], got {result}"

    def test_redact_value_none_and_primitives(self):
        """Test 36: None, bool, int, float no deben modificarse."""
        assert redact_value("test", None) is None
        assert redact_value("test", True) is True
        assert redact_value("test", False) is False
        assert redact_value("test", 42) == 42
        assert redact_value("test", 3.14) == 3.14


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])