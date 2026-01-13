"""Testes unitários para o módulo de autenticação Shopee."""

import time

import pytest

from src.shopee.auth import generate_signature, get_auth_headers


class TestGenerateSignature:
    """Testes para função generate_signature."""

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_generate_signature_valid(self):
        """Gera assinatura válida."""
        signature = generate_signature(
            app_id="123456",
            secret="demo",
            timestamp=1577836800,
            payload='{"query":"test"}',
        )

        # Verifica formato (64 caracteres hexadecimais)
        assert len(signature) == 64
        assert all(c in "0123456789abcdef" for c in signature)

    @pytest.mark.unit
    def test_generate_signature_deterministic(self):
        """Assinatura é determinística para mesmos inputs."""
        sig1 = generate_signature("123", "secret", 123456, "payload")
        sig2 = generate_signature("123", "secret", 123456, "payload")

        assert sig1 == sig2

    @pytest.mark.unit
    def test_generate_signature_different_inputs(self):
        """Inputs diferentes geram assinaturas diferentes."""
        sig1 = generate_signature("123", "secret", 123456, "payload1")
        sig2 = generate_signature("123", "secret", 123456, "payload2")

        assert sig1 != sig2

    @pytest.mark.unit
    def test_generate_signature_invalid_app_id(self):
        """Valida app_id."""
        with pytest.raises(ValueError, match="app_id"):
            generate_signature("", "secret", 123, "payload")

        with pytest.raises(ValueError, match="app_id"):
            generate_signature(None, "secret", 123, "payload")

    @pytest.mark.unit
    def test_generate_signature_invalid_secret(self):
        """Valida secret."""
        with pytest.raises(ValueError, match="secret"):
            generate_signature("app", "", 123, "payload")

        with pytest.raises(ValueError, match="secret"):
            generate_signature("app", None, 123, "payload")

    @pytest.mark.unit
    def test_generate_signature_invalid_payload(self):
        """Valida payload."""
        with pytest.raises(ValueError, match="payload"):
            generate_signature("app", "secret", 123, "")

        with pytest.raises(ValueError, match="payload"):
            generate_signature("app", "secret", 123, None)

    @pytest.mark.unit
    def test_generate_signature_invalid_timestamp(self):
        """Valida timestamp."""
        with pytest.raises(ValueError, match="timestamp"):
            generate_signature("app", "secret", -1, "payload")

        with pytest.raises(ValueError, match="timestamp"):
            generate_signature("app", "secret", 1.5, "payload")

    @pytest.mark.unit
    def test_generate_signature_known_vector(self):
        """Testa contra vetor conhecido da documentação Shopee."""
        # Da docs.md: AppId=123456, Timestamp=1577836800, Payload={"query":"..."}, Secret=demo
        # Resultado esperado: dc88d72feea70c80c52c3399751a7d34966763f51a7f056aa070a5e9df645412
        payload = '{"query":"{\\nbrandOffer{\\n    nodes{\\n        commissionRate\\n        offerName\\n    }\\n}\\n}"}'

        signature = generate_signature("123456", "demo", 1577836800, payload)

        assert signature == "dc88d72feea70c80c52c3399751a7d34966763f51a7f056aa070a5e9df645412"


class TestGetAuthHeaders:
    """Testes para função get_auth_headers."""

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_get_auth_headers_structure(self):
        """Retorna headers com estrutura correta."""
        headers = get_auth_headers("123456", "secret", '{"query":"test"}')

        assert "Authorization" in headers
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.unit
    def test_get_auth_headers_authorization_format(self):
        """Formata header Authorization corretamente."""
        headers = get_auth_headers("123456", "secret", '{"query":"test"}')

        auth = headers["Authorization"]
        assert auth.startswith("SHA256 Credential=")
        assert "Timestamp=" in auth
        assert "Signature=" in auth

    @pytest.mark.unit
    def test_get_auth_headers_components(self):
        """Header contém Credential, Timestamp e Signature."""
        headers = get_auth_headers("APP123", "SECRET456", '{"query":"test"}')

        auth = headers["Authorization"]

        # Extrai componentes
        parts = auth.split(", ")
        assert len(parts) == 3

        credential = parts[0].split("=")[1]
        timestamp = parts[1].split("=")[1]
        signature = parts[2].split("=")[1]

        assert credential == "APP123"
        assert timestamp.isdigit()
        assert len(signature) == 64  # SHA256 hex

    @pytest.mark.unit
    def test_get_auth_headers_timestamp_recent(self):
        """Timestamp deve ser recente (últimos 10 segundos)."""
        before = int(time.time())
        headers = get_auth_headers("123", "secret", '{"query":"test"}')
        after = int(time.time()) + 1  # +1 para margem

        auth = headers["Authorization"]
        timestamp_str = auth.split("Timestamp=")[1].split(",")[0]
        timestamp = int(timestamp_str)

        assert before <= timestamp <= after

    @pytest.mark.unit
    def test_get_auth_headers_signature_matches(self):
        """Signature no header corresponde à assinatura gerada."""
        payload = '{"query":"test"}'
        app_id = "123456"
        secret = "mysecret"

        headers = get_auth_headers(app_id, secret, payload)

        auth = headers["Authorization"]
        signature_from_header = auth.split("Signature=")[1]

        # Gera signature separadamente
        timestamp = int(auth.split("Timestamp=")[1].split(",")[0])
        expected_signature = generate_signature(app_id, secret, timestamp, payload)

        assert signature_from_header == expected_signature
