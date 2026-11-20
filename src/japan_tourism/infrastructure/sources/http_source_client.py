import math
from collections.abc import Generator
from contextlib import contextmanager
from email.message import Message
from pathlib import PurePosixPath
from tempfile import SpooledTemporaryFile
from typing import BinaryIO, cast
from urllib.parse import unquote, urljoin, urlsplit

import httpx

from japan_tourism.application.models.downloaded_source import (
    DownloadedSource,
)


class SourceDownloadTooLargeError(ValueError):
    """Raised when a downloaded source exceeds the configured size limit."""


class HttpSourceClient:
    """HTTP implementation of the source retrieval port."""

    CHUNK_SIZE = 1024 * 1024
    DEFAULT_SPOOL_MAX_MEMORY_BYTES = 8 * 1024 * 1024
    DEFAULT_MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
    DEFAULT_MAX_REDIRECTS = 5
    REDIRECT_STATUS_CODES = frozenset({301, 302, 303, 307, 308})

    def __init__(
        self,
        timeout: float = 30.0,
        spool_max_memory_bytes: int = DEFAULT_SPOOL_MAX_MEMORY_BYTES,
        transport: httpx.BaseTransport | None = None,
        max_download_bytes: int = DEFAULT_MAX_DOWNLOAD_BYTES,
        max_redirects: int = DEFAULT_MAX_REDIRECTS,
    ) -> None:
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("HTTP timeout must be positive and finite.")

        if spool_max_memory_bytes <= 0:
            raise ValueError("Spool memory limit must be positive.")

        if max_download_bytes <= 0:
            raise ValueError("Maximum download size must be positive.")

        if max_redirects < 0:
            raise ValueError("Maximum redirects cannot be negative.")

        self._timeout = timeout
        self._spool_max_memory_bytes = spool_max_memory_bytes
        self._transport = transport
        self._max_download_bytes = max_download_bytes
        self._max_redirects = max_redirects

    @contextmanager
    def open(
        self,
        source_url: str,
    ) -> Generator[DownloadedSource, None, None]:
        """Download a source artifact while validating every redirect."""
        self._validate_url(source_url)
        initial_origin = self._get_origin(source_url)
        current_url = source_url

        with SpooledTemporaryFile(
            max_size=self._spool_max_memory_bytes,
            mode="w+b",
        ) as temporary_file:
            with httpx.Client(
                timeout=self._timeout,
                follow_redirects=False,
                transport=self._transport,
            ) as client:
                for redirect_count in range(self._max_redirects + 1):
                    with client.stream("GET", current_url) as response:
                        if response.status_code in self.REDIRECT_STATUS_CODES:
                            location = response.headers.get("Location")

                            if not location:
                                raise httpx.HTTPStatusError(
                                    "Redirect response is missing a Location header.",
                                    request=response.request,
                                    response=response,
                                )

                            if redirect_count >= self._max_redirects:
                                raise httpx.TooManyRedirects(
                                    "Maximum redirect count exceeded.",
                                    request=response.request,
                                )

                            next_url = urljoin(str(response.url), location)
                            self._validate_url(next_url)

                            current_scheme = urlsplit(str(response.url)).scheme.lower()
                            next_scheme = urlsplit(next_url).scheme.lower()

                            if current_scheme == "https" and next_scheme == "http":
                                raise ValueError("HTTPS-to-HTTP redirects are not allowed.")

                            if self._get_origin(next_url) != initial_origin:
                                raise ValueError("Cross-origin redirects are not allowed.")

                            current_url = next_url
                            continue

                        if 300 <= response.status_code < 400:
                            raise httpx.HTTPStatusError(
                                f"Unexpected HTTP {response.status_code} response.",
                                request=response.request,
                                response=response,
                            )

                        response.raise_for_status()

                        downloaded_bytes = 0

                        for chunk in response.iter_bytes(chunk_size=self.CHUNK_SIZE):
                            downloaded_bytes += len(chunk)

                            if downloaded_bytes > self._max_download_bytes:
                                raise SourceDownloadTooLargeError(
                                    "Source download exceeded the maximum "
                                    "allowed size of "
                                    f"{self._max_download_bytes} bytes."
                                )

                            temporary_file.write(chunk)

                        original_filename = self._extract_filename(response)
                        effective_url = str(response.url)
                        break
                else:
                    raise httpx.TooManyRedirects("Maximum redirect count exceeded.")

            temporary_file.seek(0)

            yield DownloadedSource(
                stream=cast(BinaryIO, temporary_file),
                original_filename=original_filename,
                source_url=effective_url,
            )

    @staticmethod
    def _get_origin(source_url: str) -> tuple[str, str, int]:
        parsed_url = urlsplit(source_url)

        scheme = parsed_url.scheme.lower()
        hostname = parsed_url.hostname

        if hostname is None:
            raise ValueError("Source URL must contain a hostname.")

        port = parsed_url.port

        if port is None:
            port = 443 if scheme == "https" else 80

        return scheme, hostname.lower(), port

    @staticmethod
    def _validate_url(source_url: str) -> None:
        try:
            parsed_url = urlsplit(source_url)
            _ = parsed_url.port
        except ValueError as error:
            raise ValueError("Invalid source URL.") from error

        if (
            parsed_url.scheme.lower() not in {"http", "https"}
            or not parsed_url.hostname
            or parsed_url.username is not None
            or parsed_url.password is not None
        ):
            raise ValueError(
                "Source URL must be an HTTP or HTTPS URL "
                "with a valid hostname and no embedded credentials."
            )

    @classmethod
    def _extract_filename(cls, response: httpx.Response) -> str:
        content_disposition = response.headers.get("Content-Disposition")

        if content_disposition:
            message = Message()
            message["content-disposition"] = content_disposition
            filename = message.get_filename()

            if filename:
                safe_filename = cls._sanitize_filename(filename)
                if safe_filename:
                    return safe_filename

        url_path = urlsplit(str(response.url)).path
        filename = unquote(PurePosixPath(url_path).name)

        return cls._sanitize_filename(filename) or "download"

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        filename = filename.replace("\\", "/")
        filename = filename.rsplit("/", maxsplit=1)[-1]

        if filename in {"", ".", ".."} or "\x00" in filename:
            return ""

        return filename
