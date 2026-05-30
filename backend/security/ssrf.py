"""SSRF validation for outbound MCP and calendar requests."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from backend.logging_config import get_security_logger
from backend.metrics import record_security_violation

DEFAULT_ALLOWLIST: tuple[str, ...] = ("*.googleapis.com",)


class SSRFValidationError(ValueError):
    """Raised when an outbound URL fails SSRF checks."""


class SSRFValidator:
    """Validate outbound URLs against allowlists and block private networks."""

    def __init__(self, *, allowlist: tuple[str, ...] = DEFAULT_ALLOWLIST) -> None:
        self._allowlist = allowlist

    def validate_url(self, url: str, *, source: str = "mcp") -> None:
        parsed = urlparse(url)
        scheme = (parsed.scheme or "").lower()
        if scheme not in {"http", "https"}:
            self._block(url=url, reason="invalid_scheme", source=source)
            msg = f"SSRF blocked: invalid scheme in {url}"
            raise SSRFValidationError(msg)

        hostname = parsed.hostname
        if not hostname:
            self._block(url=url, reason="missing_hostname", source=source)
            msg = f"SSRF blocked: missing hostname in {url}"
            raise SSRFValidationError(msg)

        if self._is_private_host(hostname):
            self._block(url=url, reason="private_ip", source=source)
            msg = f"SSRF blocked: private host {hostname}"
            raise SSRFValidationError(msg)

        if not self._hostname_allowed(hostname):
            self._block(url=url, reason="allowlist", source=source)
            msg = f"SSRF blocked: disallowed host {hostname}"
            raise SSRFValidationError(msg)

    def validate_payload_urls(
        self,
        payload: dict[str, object],
        *,
        keys: tuple[str, ...] = ("url", "source_url", "api_url"),
        source: str = "mcp",
    ) -> None:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str) and value:
                self.validate_url(value, source=source)

    def _hostname_allowed(self, hostname: str) -> bool:
        import fnmatch

        return any(fnmatch.fnmatch(hostname, pattern) for pattern in self._allowlist)

    @staticmethod
    def _is_private_host(hostname: str) -> bool:
        try:
            infos = socket.getaddrinfo(hostname, None)
        except OSError:
            return False
        for info in infos:
            ip = info[4][0]
            try:
                if ipaddress.ip_address(ip).is_private:
                    return True
            except ValueError:
                continue
        return False

    def _block(self, *, url: str, reason: str, source: str) -> None:
        logger = get_security_logger()
        logger.warning(
            "ssrf_blocked",
            url=url,
            reason=reason,
            source=source,
        )
        record_security_violation(violation_type=f"ssrf_{reason}", agent_id=source)
