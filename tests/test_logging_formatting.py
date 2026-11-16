"""Pruebas para el formateo de stack en JsonFormatter.

Verifican que los registros JSON incluyan el campo stack cuando
stack_info está presente y que lo omitan cuando no existe.
"""

import json
import logging
import sys

from src.core.logging_config import JsonFormatter, _format_exception


class TestFormatException:
    """Pruebas para _format_exception()."""

    def test_formato_excepcion_basico(self):
        """Test: Formateo básico de excepción debe retornar string."""
        try:
            raise ValueError("error de prueba")
        except Exception:
            exc_info = sys.exc_info()
            result = _format_exception(exc_info)
            assert isinstance(result, str), f"Expected str, got {type(result)}"

    def test_formato_excepcion_incluye_tipo(self):
        """Test: El formateo debe incluir el tipo de excepción."""
        try:
            raise ValueError("error de prueba")
        except Exception:
            exc_info = sys.exc_info()
            result = _format_exception(exc_info)
            assert "ValueError" in result, f"Expected 'ValueError' in exception format, got: {result}"

    def test_formato_excepcion_incluye_mensaje(self):
        """Test: El formateo debe incluir el mensaje de la excepción."""
        try:
            raise ValueError("error de prueba")
        except Exception:
            exc_info = sys.exc_info()
            result = _format_exception(exc_info)
            assert "error de prueba" in result, f"Expected message in exception format, got: {result}"

    def test_formato_excepcion_incluye_traceback(self):
        """Test: El formateo debe incluir el traceback."""
        try:
            raise ValueError("error de prueba")
        except Exception:
            exc_info = sys.exc_info()
            result = _format_exception(exc_info)
            assert "Traceback" in result or "line" in result.lower(), (
                f"Expected traceback in exception format, got: {result}"
            )


class TestFormatStack:
    """Pruebas para el formateo de stack en JsonFormatter.

    Estas pruebas verifican el comportamiento esperado de stack_info en
    los registros JSON, aunque _format_stack() no esté implementado en
    producción (lo que provocará que las pruebas falten por defecto de
    implementación, no por error de importación).
    """

    def test_json_formato_stack_presente(self):
        """Test: JsonFormatter.format() con stack_info debe incluir campo 'stack' en JSON."""
        import logging

        logger = logging.getLogger("test_stack_presente")
        logger.setLevel(logging.ERROR)

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter(service_name="test-service"))
        logger.addHandler(handler)

        record = logging.LogRecord(
            name="test_stack_presente",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="test message",
            args=(),
            sinfo="Error en la pila de pruebas",
            exc_info=None,
        )

        formatted = handler.format(record)
        # Debe ser JSON válido
        parsed = json.loads(formatted)
        # El campo 'stack' debe estar presente cuando stack_info no es None
        assert "stack" in parsed, (
            f"Expected 'stack' key in JSON when stack_info is present, got: {formatted}"
        )
        assert isinstance(parsed["stack"], str), (
            f"Expected 'stack' to be str, got {type(parsed['stack'])}"
        )

    def test_json_sin_campo_stack_cuando_no_hay_stack_info(self):
        """Test: JSON sin stack_info no debe tener campo 'stack'."""
        import logging

        logger = logging.getLogger("test_stack_ausente")
        logger.setLevel(logging.ERROR)

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter(service_name="test-service"))
        logger.addHandler(handler)

        record = logging.LogRecord(
            name="test_stack_ausente",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="test message",
            args=(),
            sinfo=None,
            exc_info=None,
        )

        formatted = handler.format(record)
        parsed = json.loads(formatted)
        # El campo 'stack' debe ausentarse cuando stack_info es None
        assert "stack" not in parsed, (
            f"Expected no 'stack' key when stack_info is None, got: {formatted}"
        )


class TestJsonFormatterException:
    """Pruebas para JsonFormatter con excepciones."""

    def test_json_formato_excepcion(self):
        """Test: JsonFormatter.format() con exc_info debe producir JSON válido."""
        try:
            raise ValueError("error de prueba")
        except Exception:
            import logging

            logger = logging.getLogger("test_exception")
            logger.setLevel(logging.ERROR)

            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(JsonFormatter(service_name="test-service"))
            logger.addHandler(handler)

            record = logging.LogRecord(
                name="test_exception",
                level=logging.ERROR,
                pathname=__file__,
                lineno=1,
                msg="test message",
                args=(),
                exc_info=sys.exc_info(),
            )

            formatted = handler.format(record)
            # Debe ser JSON válido
            parsed = json.loads(formatted)
            assert "exception" in parsed, f"Expected 'exception' key in JSON, got: {formatted}"
            assert isinstance(parsed["exception"], str), (
                f"Expected 'exception' to be str, got {type(parsed['exception'])}"
            )

    def test_json_formato_excepcion_tipo_mensaje(self):
        """Test: JSON debe conservar tipo y mensaje de la excepción."""
        try:
            raise ValueError("error de prueba")
        except Exception:
            import logging

            logger = logging.getLogger("test_exception_type")
            logger.setLevel(logging.ERROR)

            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(JsonFormatter(service_name="test-service"))
            logger.addHandler(handler)

            record = logging.LogRecord(
                name="test_exception_type",
                level=logging.ERROR,
                pathname=__file__,
                lineno=1,
                msg="test message",
                args=(),
                exc_info=sys.exc_info(),
            )

            formatted = handler.format(record)
            parsed = json.loads(formatted)
            exception_str = parsed["exception"]
            assert "ValueError" in exception_str, f"Expected 'ValueError' in exception, got: {exception_str}"
            assert "error de prueba" in exception_str, (
                f"Expected 'error de prueba' in exception, got: {exception_str}"
            )

    def test_json_formato_excepcion_traceback(self):
        """Test: JSON debe incluir traceback de la excepción."""
        try:
            raise ValueError("error de prueba")
        except Exception:
            import logging

            logger = logging.getLogger("test_exception_traceback")
            logger.setLevel(logging.ERROR)

            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(JsonFormatter(service_name="test-service"))
            logger.addHandler(handler)

            record = logging.LogRecord(
                name="test_exception_traceback",
                level=logging.ERROR,
                pathname=__file__,
                lineno=1,
                msg="test message",
                args=(),
                exc_info=sys.exc_info(),
            )

            formatted = handler.format(record)
            parsed = json.loads(formatted)
            exception_str = parsed["exception"]
            assert (
                "Traceback" in exception_str or "line" in exception_str.lower()
            ), f"Expected traceback in exception, got: {exception_str}"


class TestJsonFormatterStackInfo:
    """Pruebas para JsonFormatter con stack_info."""

    def test_json_formato_stack_info(self):
        """Test: JsonFormatter.format() con stack_info debe producir JSON válido."""
        import logging

        logger = logging.getLogger("test_stack_info")
        logger.setLevel(logging.ERROR)

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter(service_name="test-service"))
        logger.addHandler(handler)

        record = logging.LogRecord(
            name="test_stack_info",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="test message",
            args=(),
            sinfo=None,
            exc_info=None,
        )

        # Agregar stack_info manualmente
        record.stack_info = "Test stack info"

        formatted = handler.format(record)
        # Debe ser JSON válido
        parsed = json.loads(formatted)
        assert "stack" in parsed, f"Expected 'stack' key in JSON, got: {formatted}"
        assert isinstance(parsed["stack"], str), (
            f"Expected 'stack' to be str, got {type(parsed['stack'])}"
        )

    def test_json_formato_stack_info_vacio(self):
        """Test: JSON sin stack_info no debe tener campo stack."""
        import logging

        logger = logging.getLogger("test_stack_info_vacio")
        logger.setLevel(logging.ERROR)

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter(service_name="test-service"))
        logger.addHandler(handler)

        record = logging.LogRecord(
            name="test_stack_info_vacio",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="test message",
            args=(),
            sinfo=None,
            exc_info=None,
        )

        formatted = handler.format(record)
        parsed = json.loads(formatted)
        assert "stack" not in parsed, f"Expected no 'stack' key when stack_info is None, got: {formatted}"


class TestRedactionInExceptions:
    """Pruebas para redacción de credenciales y parámetros en excepciones."""

    def test_redaccion_uri_dentro_excepcion(self):
        """Test: Las credenciales en URI dentro de excepciones deben redactarse."""
        try:
            raise ValueError("mongodb://usuario:clave@db:27017/db")
        except Exception:
            import logging

            logger = logging.getLogger("test_uri_in_exception")
            logger.setLevel(logging.ERROR)

            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(JsonFormatter(service_name="test-service"))
            logger.addHandler(handler)

            record = logging.LogRecord(
                name="test_uri_in_exception",
                level=logging.ERROR,
                pathname=__file__,
                lineno=1,
                msg="test message",
                args=(),
                exc_info=sys.exc_info(),
            )

            formatted = handler.format(record)
            parsed = json.loads(formatted)
            exception_str = parsed["exception"]
            # Las credenciales deben estar redactadas como ***
            assert "***:***@" in exception_str or "mongodb://***:**@" in exception_str, (
                f"Expected redacted credentials in exception, got: {exception_str}"
            )

    def test_redaccion_parametros_uri_dentro_excepcion(self):
        """Test: Los parámetros sensibles en URI dentro de excepciones deben redactarse."""
        try:
            raise ValueError("https://api.example.com/?token=abc123&secret=xyz")
        except Exception:
            import logging

            logger = logging.getLogger("test_params_in_exception")
            logger.setLevel(logging.ERROR)

            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(JsonFormatter(service_name="test-service"))
            logger.addHandler(handler)

            record = logging.LogRecord(
                name="test_params_in_exception",
                level=logging.ERROR,
                pathname=__file__,
                lineno=1,
                msg="test message",
                args=(),
                exc_info=sys.exc_info(),
            )

            formatted = handler.format(record)
            parsed = json.loads(formatted)
            exception_str = parsed["exception"]
            # token y secret deben estar redactados
            assert "token=***" in exception_str, f"Expected 'token=***', got: {exception_str}"
            assert "secret=***" in exception_str, f"Expected 'secret=***', got: {exception_str}"

    def test_redaccion_uri_dentro_stack_info(self):
        """Test: Las credenciales en URI dentro de stack_info deben redactarse."""
        import logging

        logger = logging.getLogger("test_uri_in_stack")
        logger.setLevel(logging.ERROR)

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter(service_name="test-service"))
        logger.addHandler(handler)

        record = logging.LogRecord(
            name="test_uri_in_stack",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="test message",
            args=(),
            sinfo="Error en mongodb://usuario:clave@db:27017/db",
            exc_info=None,
        )

        formatted = handler.format(record)
        parsed = json.loads(formatted)
        stack_str = parsed["stack"]
        # Las credenciales deben estar redactadas
        assert "***:***@" in stack_str or "mongodb://***:**@" in stack_str, (
            f"Expected redacted credentials in stack, got: {stack_str}"
        )


class TestValidJSON:
    """Pruebas devalidación que cada resultado sea JSON válido."""

    def test_json_excepcion_valido(self):
        """Test: El formateo de excepción siempre debe producir JSON válido."""
        try:
            raise ValueError("error de prueba")
        except Exception:
            import logging

            logger = logging.getLogger("test_valid_json")
            logger.setLevel(logging.ERROR)

            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(JsonFormatter(service_name="test-service"))
            logger.addHandler(handler)

            record = logging.LogRecord(
                name="test_valid_json",
                level=logging.ERROR,
                pathname=__file__,
                lineno=1,
                msg="test message",
                args=(),
                exc_info=sys.exc_info(),
            )

            formatted = handler.format(record)
            # Debe poder parsearse como JSON
            parsed = json.loads(formatted)
            assert isinstance(parsed, dict), f"Expected dict from JSON, got: {formatted}"
            assert "timestamp" in parsed, f"Expected 'timestamp' key in JSON, got: {formatted}"
            assert "level" in parsed, f"Expected 'level' key in JSON, got: {formatted}"
            assert "service" in parsed, f"Expected 'service' key in JSON, got: {formatted}"
            assert "message" in parsed, f"Expected 'message' key in JSON, got: {formatted}"

    def test_json_con_stack_info_valido(self):
        """Test: El formateo con stack_info debe producir JSON válido."""
        import logging

        logger = logging.getLogger("test_json_stack_valid")
        logger.setLevel(logging.ERROR)

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter(service_name="test-service"))
        logger.addHandler(handler)

        record = logging.LogRecord(
            name="test_json_stack_valid",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="test message",
            args=(),
            sinfo="Test stack info",
            exc_info=None,
        )

        formatted = handler.format(record)
        parsed = json.loads(formatted)
        assert isinstance(parsed, dict), f"Expected dict from JSON, got: {formatted}"
        assert "timestamp" in parsed, f"Expected 'timestamp' key in JSON, got: {formatted}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])