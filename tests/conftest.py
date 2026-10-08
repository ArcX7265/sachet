"""Optional API regression run against an explicitly disposable PostgreSQL DB."""
import os
import pytest


@pytest.fixture(autouse=True)
def database_environment(monkeypatch):
    # Never let a developer's production DATABASE_URL leak into tests.
    url = os.getenv("SACHET_TEST_DATABASE_URL")
    monkeypatch.delenv("VERCEL", raising=False)
    if not url:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        return
    from urllib.parse import urlparse
    if not urlparse(url).path.rsplit('/', 1)[-1].endswith('_test'):
        pytest.fail("SACHET_TEST_DATABASE_URL must name a disposable database ending in _test.")
    monkeypatch.setenv("DATABASE_URL", url)
    from app import main
    main.init_db()
    with main.db(write=True) as c:
        c.execute("TRUNCATE sessions,cases,events,assessments,alerts,candidates,contributions,bundles,payments,orders,order_attempts,gateway_events,provider_calls,audit,accounts,login_attempts RESTART IDENTITY CASCADE")
    main.init_db()
