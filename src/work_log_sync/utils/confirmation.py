"""Confirmation utility for API calls."""

import json
import logging
from typing import Any

import httpx
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()


def _redact_sensitive_data(text: str) -> str:
    """Redact sensitive data from strings like tokens and API keys.

    Args:
        text: Text that may contain sensitive data.

    Returns:
        Text with sensitive data redacted.
    """
    # Redact API keys, tokens, etc. - keep first 4 and last 4 chars
    if len(text) <= 8:
        return "****"

    return f"{text[:4]}...{text[-4:]}"


def _redact_headers(headers: dict[str, str]) -> dict[str, str]:
    """Redact sensitive headers like Authorization and X-Api-Key.

    Args:
        headers: Original headers dictionary.

    Returns:
        Dictionary with sensitive values redacted.
    """
    sensitive_keys = {"authorization", "x-api-key", "x-access-token", "cookie"}
    redacted = {}

    for key, value in headers.items():
        if key.lower() in sensitive_keys:
            redacted[key] = _redact_sensitive_data(value)
        else:
            redacted[key] = value

    return redacted


def _format_payload(data: Any) -> str:
    """Format request payload for display.

    Args:
        data: Request payload (dict, bytes, or other).

    Returns:
        Formatted payload string.
    """
    if isinstance(data, bytes):
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return "[binary data]"

    if isinstance(data, dict):
        try:
            return json.dumps(data, indent=2)
        except (TypeError, ValueError):
            return str(data)

    return str(data) if data else "[no payload]"


def _prompt_for_confirmation() -> bool:
    """Prompt user for confirmation to proceed with API call.

    Returns:
        True if user confirms (y), False if user declines (n).
        Exits if user wants to abort.
    """
    while True:
        response = console.input(
            "[bold cyan]Proceed with this API call? [y/n][/bold cyan] "
        ).strip().lower()

        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False
        else:
            console.print("[yellow]Please enter 'y' or 'n'[/yellow]")


class ConfirmationTransport(httpx.BaseTransport):
    """Custom httpx transport that prompts for confirmation before each request."""

    def __init__(self, transport: httpx.BaseTransport) -> None:
        """Initialize confirmation transport with underlying transport.

        Args:
            transport: The underlying httpx transport to wrap.
        """
        self.transport = transport

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """Handle request with confirmation prompt.

        Args:
            request: The HTTP request.

        Returns:
            The HTTP response.

        Raises:
            httpx.RequestError: If user declines confirmation.
        """
        # Display request details
        console.print("\n" + "=" * 80)
        console.print(f"[bold blue]API Request[/bold blue]")
        console.print("=" * 80)

        # Show method and URL
        console.print(f"[bold cyan]Method:[/bold cyan] {request.method}")
        console.print(f"[bold cyan]URL:[/bold cyan] {request.url}")

        # Show headers (redacted)
        if request.headers:
            redacted_headers = _redact_headers(dict(request.headers))
            table = Table(title="Headers", show_header=True, header_style="bold magenta")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")

            for key, value in redacted_headers.items():
                table.add_row(key, value)

            console.print(table)

        # Show payload if present
        if request.content:
            payload_str = _format_payload(request.content)
            console.print(f"\n[bold cyan]Payload:[/bold cyan]")
            if payload_str.startswith("{"):
                # Format as syntax-highlighted JSON
                syntax = Syntax(payload_str, "json", theme="monokai", line_numbers=False)
                console.print(syntax)
            else:
                console.print(payload_str)

        console.print("=" * 80)

        # Prompt for confirmation
        if not _prompt_for_confirmation():
            console.print("[bold red]✗ API call cancelled by user[/bold red]\n")
            raise httpx.RequestError("API call cancelled by user")

        # Proceed with actual request
        console.print("[bold green]✓ Proceeding with API call[/bold green]\n")
        return self.transport.handle_request(request)


def create_confirming_client(
    base_url: str | None = None,
    headers: dict[str, str] | None = None,
    **kwargs: Any,
) -> httpx.Client:
    """Create an httpx client with confirmation prompts.

    Args:
        base_url: Base URL for the client.
        headers: Default headers for requests.
        **kwargs: Additional arguments passed to httpx.Client.

    Returns:
        httpx.Client configured with confirmation transport.
    """
    # Create transport with confirmation wrapper
    default_transport = httpx.HTTPTransport()
    confirming_transport = ConfirmationTransport(default_transport)

    return httpx.Client(
        base_url=base_url,
        headers=headers,
        transport=confirming_transport,
        **kwargs,
    )
