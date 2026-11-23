import os
import urllib.request
import pytest

playwright_sync = pytest.importorskip(
    "playwright.sync_api",
    reason="Install playwright to run browser E2E tests",
)
expect = playwright_sync.expect
sync_playwright = playwright_sync.sync_playwright

TRUSTDESK_URL = os.getenv("TRUSTDESK_URL", "http://localhost:3000")


def _trustdesk_is_reachable(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _trustdesk_is_reachable(TRUSTDESK_URL),
    reason=f"TrustDesk UI not running at {TRUSTDESK_URL}",
)


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(headless=True)
        except Exception:
            b = p.chromium.launch(headless=True, channel="chrome")
        yield b
        b.close()


@pytest.fixture(scope="function")
def page(browser):
    ctx = browser.new_context(viewport={"width": 1280, "height": 720})
    pg = ctx.new_page()
    yield pg
    ctx.close()


def test_channel_toggle_and_ephemeral_token_state(page):
    page.goto(TRUSTDESK_URL, wait_until="domcontentloaded")
    untrusted_btn = page.get_by_role("button", name="Untrusted (Public)")
    trusted_btn = page.get_by_role("button", name="Trusted (Internal)")
    bearer_input = page.get_by_label("Trusted channel Bearer token")

    expect(untrusted_btn).to_have_attribute("aria-pressed", "true")
    expect(bearer_input).to_be_hidden()

    trusted_btn.click()
    expect(trusted_btn).to_have_attribute("aria-pressed", "true")
    expect(bearer_input).to_be_visible()
    bearer_input.fill("ephemeral-test-token")

    stored_keys = page.evaluate("() => Object.keys(window.localStorage)")
    assert "ephemeral-test-token" not in str(stored_keys)

    untrusted_btn.click()
    expect(bearer_input).to_be_hidden()


def test_send_loan_faq_streams_assistant_response(page):
    page.goto(TRUSTDESK_URL, wait_until="domcontentloaded")
    query = "What is the synthetic home loan interest rate and minimum tenure?"
    query_input = page.get_by_label("Ask a loan question")
    send_btn = page.get_by_role("button", name="Send query")

    query_input.fill(query)
    send_btn.click()

    expect(page.get_by_text(query)).to_be_visible()
    expect(query_input).to_be_enabled(timeout=15000)
    expect(page.locator("body")).to_contain_text("%", timeout=15000)


def test_trusted_channel_without_token_shows_401_error(page):
    page.goto(TRUSTDESK_URL, wait_until="domcontentloaded")
    page.get_by_role("button", name="Trusted (Internal)").click()
    page.get_by_label("Ask a loan question").fill("Check internal policy details.")
    page.get_by_role("button", name="Send query").click()

    expect(page.get_by_text("Channel Authorization Failure (HTTP 401)")).to_be_visible(timeout=10000)
