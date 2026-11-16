"""Tests automatizados para la redacción de datos sensibles en MS2.

Cubre las funciones is_sensitive_key(), redact_value() y redact_uri()
del módulo src.core.logging_config, según la especificación del
Factor 11 (12-Factor App logging).
"""

from src.core.logging_config import is_sensitive_key, redact_value, redact_uri


class TestIsSensitiveKey:
    """Tests para la función is_sensitive_key().

    Esta función determina si una clave debe tratarse como sensible
    basándose en el nombre de la clave normalizado y la coincidencia con
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
        # Con prefijos y sufijos habituales
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
        """Test 1-10: Las claves sensibles literales deben reconocerse."""
        for key in self.SENSITIVE_LITERALS:
            result = is_sensitive_key(key)
            assert result is True, f"Expected '{key}' to be sensitive, got {result}"

    def test_sensitive_variants_with_case(self):
        """Test 11-18: Las variantes de mayúsculas/minúsculas deben reconocerse."""
        for key in self.SENSITIVE_VARIANTS:
            result = is_sensitive_key(key)
            assert result is True, f"Expected '{key}' to be sensitive, got {result}"

    def test_insensitive_keys_rejected(self):
        """Test 19: Las claves no sensibles deben rechazarse."""
        for key in self.INSENSITIVE_KEYS:
            result = is_sensitive_key(key)
            assert result is False, f"Expected '{key}' to be insensitive, got {result}"

    def test_variants_with_underscores(self):
        """Test 20-21: Las variantes con guion bajo deben reconocerse."""
        # access_token y api_key ya están en SENSITIVE_LITERALS,
        # pero probamos específicamente la variante con guion bajo.
        assert is_sensitive_key("access_token") is True
        assert is_sensitive_key("api_key") is True

    def test_variants_with_hyphens(self):
        """Test 22-24: Las variantes con guiones deben reconocerse."""
        assert is_sensitive_key("api-key") is True
        assert is_sensitive_key("access-token") is True
        assert is_sensitive_key("private-key") is True

    def test_suffixes_and_prefixes(self):
        """Test 25-30: Los prefijos y sufijos habituales deben reconocerse."""
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

    Esta función reemplaza por "***" los valores asociados a claves sensibles
    y conserva los valores asociados a claves no sensibles.
    """

    def test_sensitive_key_redacted(self):
        """Test 31: El valor asociado a una clave sensible debe ser ***."""
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
        """Test 32: El valor asociado a una clave no sensible debe conservarse."""
        # endpoint
        result = redact_value("endpoint", "/api/v1/users")
        assert result == "/api/v1/users", f"Expected '/api/v1/users', got {result}"

        # request_id
        result = redact_value("request_id", "req-998877")
        assert result == "req-998877", f"Expected 'req-998877', got {result}"

        # message (no es una clave de contexto típica, pero se incluye en la prueba)
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
        # password y api_key deben redactarse
        assert result["password"] == "***", f"Expected password to be redacted, got {result['password']}"
        assert result["api_key"] == "***", f"Expected api_key to be redacted, got {result['api_key']}"
        # url y endpoint deben conservarse
        assert result["url"] == "mongodb://host:27017", f"Expected url unchanged, got {result['url']}"
        assert result["endpoint"] == "/health", f"Expected endpoint unchanged, got {result['endpoint']}"

    def test_redact_value_sensitive_key_immediate_redact(self):
        """Test 34: Una clave sensible devuelve *** inmediatamente, sin recursión.

        El comportamiento actual de redact_value() es devolver "***"
        inmediatamente cuando la clave es sensible, sin inspeccionar el
        valor o la estructura del mismo.
        """
        result = redact_value("password", {"db_password": "internal", "host": "localhost"})
        assert result == "***", f"Expected '***', got {result}"

    def test_redact_value_with_list(self):
        """Test 35: Lista de valores asociada a una clave no sensible.

        Cuando redact_value recibe una lista (o tupla, set o frozenset), itera
        sobre cada elemento aplicando la lógica de redacción recursiva. Dado
        que los elementos son cadenas de texto y no hay una clave asociada por
        nombre (key="" vacío), las cadenas se conservan tal cual: no hay una
        clave sensible que active la redacción sobre ellas.
        """
        result = redact_value("", ["public_item", "secret_value"])
        assert result == ["public_item", "secret_value"], f"Expected ['public_item', 'secret_value'], got {result}"

    def test_redact_value_none_and_primitives(self):
        """Test 36: None, bool, int y float no deben modificarse."""
        assert redact_value("test", None) is None
        assert redact_value("test", True) is True
        assert redact_value("test", False) is False
        assert redact_value("test", 42) == 42
        assert redact_value("test", 3.14) == 3.14


class TestRedactUri:
    """Tests para la función redact_uri() del módulo src.core.logging_config.

    Esta función oculta credenciales (usuario y contraseña) en URI con esquema
    ://, conservando el esquema y el host para diagnóstico.

    Comportamiento:
    - Oculta credenciales embebidas en URI con esquema ://.
    - Oculta parámetros sensibles en cadenas de consulta (query strings).
    - Conserva los parámetros públicos y la estructura de la URI.
    - No redacta contraseñas en texto plano que no forman parte de una URI.
    """

    def test_mongodb_uri_with_credentials(self):
        """Test: Una URI MongoDB con usuario y contraseña debe redactarse."""
        result = redact_uri("mongodb://usuario:clave@db:27017/?authSource=admin")
        expected = "mongodb://***:***@db:27017/?authSource=admin"
        assert result == expected, f"Expected '{expected}', got '{result}'"

    def test_http_uri_with_credentials(self):
        """Test: Una URI HTTP con credenciales debe redactarse."""
        result = redact_uri("https://user:pass@example.com/path")
        expected = "https://***:***@example.com/path"
        assert result == expected, f"Expected '{expected}', got '{result}'"

    def test_https_uri_with_credentials(self):
        """Test: Una URI HTTPS con credenciales debe redactarse."""
        result = redact_uri("http://admin:secret@secure.example.com/api")
        expected = "http://***:***@secure.example.com/api"
        assert result == expected, f"Expected '{expected}', got '{result}'"

    def test_uri_without_credentials(self):
        """Test: Una URI sin credenciales debe conservarse sin modificaciones."""
        result = redact_uri("mongodb://host:27017/db")
        expected = "mongodb://host:27017/db"
        assert result == expected, f"Expected '{expected}', got '{result}'"

    def test_uri_empty_string(self):
        """Test: Una URI vacía debe devolver una cadena vacía."""
        result = redact_uri("")
        expected = ""
        assert result == expected, f"Expected '{expected}', got '{result}'"

    def test_uri_none(self):
        """Test: Un valor None debe devolver una cadena vacía."""
        result = redact_uri(None)
        expected = ""
        assert result == expected, f"Expected '{expected}', got '{result}'"

    def test_credentials_url_encoded(self):
        """Test: Las credenciales codificadas en URL deben redactarse."""
        result = redact_uri("https://user%40pass@example.com")
        expected = "https://***:***@example.com"
        assert result == expected, f"Expected '{expected}', got '{result}'"

    def test_custom_scheme(self):
        """Test: Las credenciales en esquemas personalizados deben redactarse."""
        result = redact_uri("custom://credencial@host")
        expected = "custom://***:***@host"
        assert result == expected, f"Expected '{expected}', got '{result}'"

    def test_uri_with_port_and_path(self):
        """Test: Una URI con puerto y ruta completos debe conservar su estructura."""
        result = redact_uri("mysql://root:password@localhost:3306/app_db")
        expected = "mysql://***:***@localhost:3306/app_db"
        assert result == expected, f"Expected '{expected}', got '{result}'"

    def test_string_not_uri(self):
        """Test: Las cadenas que no tienen formato de URI deben conservarse."""
        result = redact_uri("solo_texto_sin_formato_de_uri")
        expected = "solo_texto_sin_formato_de_uri"
        assert result == expected, f"Expected '{expected}', got '{result}'"

    def test_string_password_not_redacted_by_redact_uri(self):
        """Test: Las cadenas de texto como 'mipassword' no son URI
        y no son redactadas por redact_uri() porque no contienen ://.

        Esta prueba documenta el alcance de la función: redact_uri()
        procesa URI, no contraseñas aisladas en texto plano.
        """
        # Las cadenas de texto sin :// no son reconocidas como URI por redact_uri().
        result = redact_uri("mipassword123")
        # Al no tener esquema ://, la expresión regular no coincide y el texto se conserva.
        assert result == "mipassword123", f"Expected 'mipassword123' (no URI format), got '{result}'"
        # Esto documenta que redact_uri() no procesa contraseñas aisladas en texto plano.


class TestRedactUriQueryStrings:
    """Tests para la redacción de parámetros sensibles en cadenas de consulta.

    Verifican que redact_uri() oculte valores sensibles, conserve parámetros
    públicos y respete el orden y los parámetros repetidos.

    La identificación de claves sensibles reutiliza is_sensitive_key().
    """

    def test_token_in_query_string(self):
        """Test: Un parámetro token en la cadena de consulta debe redactarse."""
        # 'token' es una clave sensible según is_sensitive_key().
        result = redact_uri("https://api.example.com/?token=abc123xyz")
        # El parámetro token debe redactarse obligatoriamente a token=***
        assert "token=***" in result, f"Expected 'token=***' in URI, got '{result}'"

    def test_api_key_in_query_string(self):
        """Test: Un parámetro api_key en la cadena de consulta debe redactarse."""
        result = redact_uri("https://api.example.com/?api_key=sk-1234567890abcdef")
        # El parámetro api_key debe redactarse obligatoriamente a api_key=***
        assert "api_key=***" in result, f"Expected 'api_key=***' in URI, got '{result}'"

    def test_password_in_query_string(self):
        """Test: Un parámetro password en la cadena de consulta debe redactarse."""
        result = redact_uri("https://example.com/?password=secret123")
        # El parámetro password debe redactarse obligatoriamente a password=***
        assert "password=***" in result, f"Expected 'password=***' in URI, got '{result}'"

    def test_secret_and_access_token(self):
        """Test: Los parámetros secret y access_token deben redactarse."""
        result = redact_uri("https://api.example.com/?secret=mysecret&access_token=tok123")
        # Los parámetros secret y access_token deben redactarse obligatoriamente
        assert "secret=***" in result, f"Expected 'secret=***' in URI, got '{result}'"
        assert "access_token=***" in result, f"Expected 'access_token=***' in URI, got '{result}'"

    def test_multiple_sensitive_parameters(self):
        """Test: Varios parámetros sensibles en una misma URI.

        Verifica que los parámetros sensibles (token y secret) queden redactados.
        También verifica que los parámetros públicos (a y b) permanezcan intactos.
        """
        result = redact_uri("https://host/?a=1&token=2&b=3&secret=4")
        # Los parámetros sensibles deben redactarse.
        assert "token=***" in result, f"token should be redacted, got '{result}'"
        assert "secret=***" in result, f"secret should be redacted, got '{result}'"
        # Los parámetros públicos deben conservarse.
        assert "a=1" in result, f"public param 'a=1' should be conserved, got '{result}'"
        assert "b=3" in result, f"public param 'b=3' should be conserved, got '{result}'"

    def test_sensitive_mixed_with_public_parameters(self):
        """Test: Parámetros sensibles mezclados con parámetros públicos.

        Exige que token quede redactado como token=*** y que los parámetros
        públicos (public y format) se conserven intactos.
        """
        result = redact_uri("https://api.example.com/?public=value&token=secret&format=json")
        # El parámetro sensible debe redactarse.
        assert "token=***" in result, f"token should be redacted to token=***, got '{result}'"
        # Los parámetros públicos deben conservarse.
        assert "public=value" in result, f"public param should be conserved, got '{result}'"
        assert "format=json" in result, f"public param should be conserved, got '{result}'"

    def test_variants_case_insensitive(self):
        """Test: Variantes en mayúsculas y minúsculas de parámetros sensibles.

        Exige redacción tanto de TOKEN como de token, ya que is_sensitive_key()
        normaliza la clave y detecta ambas variantes. La redacción debe aplicarse
        independientemente del caso utilizado en el nombre del parámetro. Se permite
        conservar el nombre original (TOKEN=*** o token=***).
        """
        # Token en mayúsculas.
        result1 = redact_uri("https://api.example.com/?TOKEN=abc123")
        # Token en minúsculas.
        result2 = redact_uri("https://api.example.com/?token=abc123")
        # Ambos deben redactar el parámetro sensible, conservando el caso original.
        assert "TOKEN=***" in result1, f"TOKEN should be redacted to TOKEN=***, got '{result1}'"
        assert "token=***" in result2, f"token should be redacted to token=***, got '{result2}'"

    def test_variants_with_hyphens_and_underscores(self):
        """Test: Variantes con guiones y guiones bajos en nombres de parámetros.

        Exige redacción de access-token y access_token, que son variantes
        sensibles detectadas por is_sensitive_key() mediante normalización.
        """
        # access-token con guion.
        result1 = redact_uri("https://api.example.com/?access-token=abc123")
        # access_token con guion bajo.
        result2 = redact_uri("https://api.example.com/?access_token=abc123")
        # Ambos deben redactar el parámetro sensible.
        assert "access-token=***" in result1, f"access-token should be redacted, got '{result1}'"
        assert "access_token=***" in result2, f"access_token should be redacted, got '{result2}'"

    def test_repeated_parameters_preserved(self):
        """Test: Parámetros repetidos, preservando todos los valores redactados.

        Exige que los tres parámetros token continúen presentes,
        pero que sus valores estén redactados como ***.
        Ninguno de los valores originales (abc, def, ghi) debe aparecer.
        """
        result = redact_uri("https://api.example.com/?token=abc&token=def&token=ghi")
        # Los tres parámetros token deben seguir presentes (como ocurrencias de "token=").
        assert result.count("token=") == 3, f"Should have 3 token params, got '{result}'"
        # Ninguno de los valores originales debe aparecer.
        assert "abc" not in result, f"Original value 'abc' should not appear, got '{result}'"
        assert "def" not in result, f"Original value 'def' should not appear, got '{result}'"
        assert "ghi" not in result, f"Original value 'ghi' should not appear, got '{result}'"
        # Todos los valores deben estar redactados como ***.
        assert "token=***" in result, f"token values should be redacted, got '{result}'"
        # Verificación exacta: los tres parámetros token deben tener sus valores redactados.
        assert result.count("token=***") == 3, f"Expected 3 occurrences of 'token=***', got '{result}'"

    def test_url_encoded_values(self):
        """Test: Valores codificados en URL dentro de la cadena de consulta.

        Exige que el valor de token quede completamente oculto.
        El parámetro público debe conservarse.
        """
        result = redact_uri("https://api.example.com/?token=user%40host&public=value")
        # El valor del token debe redactarse.
        assert "token=***" in result, f"token value should be redacted, got '{result}'"
        # El parámetro público debe conservarse.
        assert "public=value" in result, f"public param should be conserved, got '{result}'"

    def test_credentials_and_query_simultaneously(self):
        """Test: URI con credenciales embebidas y parámetros sensibles simultáneamente.

        Exige que las credenciales embebidas sigan redactadas
        (comportamiento actual de redact_uri()) y que token y secret
        también queden ocultos en la cadena de consulta.
        """
        result = redact_uri("mongodb://user:pass@host:27017/db?token=abc123&secret=xyz")
        # Las credenciales embebidas deben continuar redactadas.
        assert "mongodb://***:***@host:27017/db" in result, (
            f"Credentials should be redacted, got '{result}'"
        )
        # Los parámetros de la cadena de consulta también deben redactarse.
        assert "token=***" in result, f"token query param should be redacted, got '{result}'"
        assert "secret=***" in result, f"secret query param should be redacted, got '{result}'"

    def test_uri_without_query_string(self):
        """Test: Una URI sin cadena de consulta debe conservar el comportamiento esperado."""
        result = redact_uri("mongodb://user:pass@host:27017/db")
        # La implementación actual oculta las credenciales.
        expected_redacted_creds = "mongodb://***:***@host:27017/db"
        assert result == expected_redacted_creds, (
            f"Expected creds redacted, got '{result}'"
        )

    def test_uri_empty_and_none(self):
        """Test: Una URI vacía y un valor None deben devolver una cadena vacía."""
        result_empty = redact_uri("")
        result_none = redact_uri(None)
        assert result_empty == "", f"Empty URI should return '', got '{result_empty}'"
        assert result_none == "", f"None URI should return '', got '{result_none}'"

    def test_public_parameters_conserved(self):
        """Test: Los parámetros públicos deben conservar sus nombres, valores y orden."""
        result = redact_uri("https://api.example.com/?a=1&b=2&c=3")
        # Los parámetros públicos deben conservarse sin modificaciones.
        assert "a=1" in result, f"Public param 'a=1' should be conserved, got '{result}'"
        assert "b=2" in result, f"Public param 'b=2' should be conserved, got '{result}'"
        assert "c=3" in result, f"Public param 'c=3' should be conserved, got '{result}'"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])