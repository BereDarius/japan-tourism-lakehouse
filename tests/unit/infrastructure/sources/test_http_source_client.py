from tempfile import SpooledTemporaryFile

import httpx
import pytest

from japan_tourism.infrastructure.sources.http_source_client import (
    HttpSourceClient,
    SourceDownloadTooLargeError,
)


def make_client(
    transport: httpx.BaseTransport,
    *,
    max_download_bytes: int = 100 * 1024 * 1024,
    spool_max_memory_bytes: int = 8 * 1024 * 1024,
) -> HttpSourceClient:
    return HttpSourceClient(
        transport=transport,
        max_download_bytes=max_download_bytes,
        spool_max_memory_bytes=spool_max_memory_bytes,
    )


def test_successful_download_preserves_bytes() -> None:
    content = b"JTA workbook content"

    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            content=content,
            request=request,
        )
    )
    client = make_client(transport)

    with client.open("https://example.com/source.xlsx") as downloaded:
        assert downloaded.stream.read() == content
        assert downloaded.original_filename == "source.xlsx"
        assert downloaded.source_url == "https://example.com/source.xlsx"


def test_redirect_records_effective_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/original":
            return httpx.Response(
                302,
                headers={"Location": "/downloads/final.xlsx"},
                request=request,
            )

        return httpx.Response(
            200,
            content=b"workbook",
            request=request,
        )

    client = make_client(httpx.MockTransport(handler))

    with client.open("https://example.com/original") as downloaded:
        assert downloaded.source_url == ("https://example.com/downloads/final.xlsx")
        assert downloaded.original_filename == "final.xlsx"


def test_content_disposition_filename_takes_precedence() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            content=b"workbook",
            headers={"Content-Disposition": 'attachment; filename="jta-data.xlsx"'},
            request=request,
        )
    )
    client = make_client(transport)

    with client.open("https://example.com/download") as downloaded:
        assert downloaded.original_filename == "jta-data.xlsx"


def test_url_filename_is_percent_decoded() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            content=b"workbook",
            request=request,
        )
    )
    client = make_client(transport)

    with client.open("https://example.com/files/JTA%20data.xlsx") as downloaded:
        assert downloaded.original_filename == "JTA data.xlsx"


def test_missing_url_filename_uses_fallback() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            content=b"workbook",
            request=request,
        )
    )
    client = make_client(transport)

    with client.open("https://example.com/") as downloaded:
        assert downloaded.original_filename == "download"


def test_http_error_is_propagated() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            404,
            request=request,
        )
    )
    client = make_client(transport)

    with pytest.raises(httpx.HTTPStatusError):
        with client.open("https://example.com/missing.xlsx"):
            pass


@pytest.mark.parametrize(
    "source_url",
    [
        "ftp://example.com/source.xlsx",
        "file:///tmp/source.xlsx",
        "https://user:password@example.com/source.xlsx",
        "https:///missing-host.xlsx",
    ],
)
def test_invalid_url_is_rejected(source_url: str) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, request=request))
    client = make_client(transport)

    with pytest.raises(ValueError):
        with client.open(source_url):
            pass


def test_download_exactly_at_limit_is_accepted() -> None:
    content = b"12345"
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            content=content,
            request=request,
        )
    )
    client = make_client(transport, max_download_bytes=5)

    with client.open("https://example.com/source.xlsx") as downloaded:
        assert downloaded.stream.read() == content


def test_download_above_limit_is_rejected() -> None:
    content = b"123456"
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            content=content,
            request=request,
        )
    )
    client = make_client(transport, max_download_bytes=5)

    with pytest.raises(SourceDownloadTooLargeError):
        with client.open("https://example.com/source.xlsx"):
            pass


def test_large_download_spools_to_disk() -> None:
    content = b"x" * 100
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            content=content,
            request=request,
        )
    )
    client = make_client(
        transport,
        spool_max_memory_bytes=10,
    )

    with client.open("https://example.com/source.xlsx") as downloaded:
        assert isinstance(downloaded.stream, SpooledTemporaryFile)
        assert downloaded.stream.read() == content


def test_invalid_configuration_is_rejected() -> None:
    with pytest.raises(ValueError, match="Maximum download size"):
        HttpSourceClient(max_download_bytes=0)

    with pytest.raises(ValueError, match="HTTP timeout"):
        HttpSourceClient(timeout=0)

    with pytest.raises(ValueError, match="Spool memory limit"):
        HttpSourceClient(spool_max_memory_bytes=0)


def test_response_is_closed_after_download_failure() -> None:
    response: httpx.Response | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal response
        response = httpx.Response(
            200,
            content=b"123456",
            request=request,
        )
        return response

    client = make_client(
        httpx.MockTransport(handler),
        max_download_bytes=5,
    )

    with pytest.raises(SourceDownloadTooLargeError):
        with client.open("https://example.com/source.xlsx"):
            pass

    assert response is not None
    assert response.is_closed
