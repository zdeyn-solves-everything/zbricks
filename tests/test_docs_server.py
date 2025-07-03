import pytest
from starlette.testclient import TestClient

from zbricks.docs.serve import create_app


def make_fake_docs(tmp_path):
    content_dir = tmp_path / "content"
    theme_dir = tmp_path / "theme"
    site_yaml = tmp_path / "site.yaml"
    content_dir.mkdir()
    theme_dir.mkdir()
    (content_dir / "example1.md").write_text(
        "---\n"
        "title: Example 1\n"
        "slug: example1\n"
        "---\n\n"
        "# Example 1\n\n"
        "This is the first example document.\n"
    )
    (content_dir / "example2.md").write_text(
        "---\n"
        "title: Example 2\n"
        "slug: example2\n"
        "---\n\n"
        "# Example 2\n\n"
        "This is the second example document.\n"
    )
    # Minimal theme: no blocks, just output title and content
    (theme_dir / "base.html").write_text(
        "<!DOCTYPE html><html><head><title>{{ doc.title if doc else 'Docs' }}</title>"
        "</head><body>{{ content|safe }}</body></html>"
    )
    (theme_dir / "index.html").write_text(
        "<ul>"
        "{% for doc in docs %}"
        "<li><a href='/{{ doc.slug }}'>{{ doc.title }}</a></li>"
        "{% endfor %}"
        "</ul>"
    )
    (theme_dir / "doc.html").write_text(
        "<h1>{{ doc.title }}</h1>{{ content|safe }}"
    )
    # Minimal site.yaml
    site_yaml.write_text(
        "nav:\n"
        "  - title: Example 1\n"
        "    slug: example1\n"
        "    doc: example1\n"
        "  - title: Example 2\n"
        "    slug: example2\n"
        "    doc: example2\n"
    )
    return str(content_dir), str(theme_dir), str(site_yaml)

@pytest.fixture
def fake_env(tmp_path):
    content_dir, theme_dir, site_yaml = make_fake_docs(tmp_path)
    app = create_app(content_dir, theme_dir, site_yaml_path=site_yaml)
    return TestClient(app)

def test_index(fake_env):
    client = fake_env
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Example 1" in resp.text
    assert "Example 2" in resp.text
    assert "/example1" in resp.text
    assert "/example2" in resp.text

def test_doc_pages(fake_env):
    client = fake_env
    for slug, title in [("example1", "Example 1"), ("example2", "Example 2")]:
        resp = client.get(f"/{slug}")
        assert resp.status_code == 200
        assert f"<h1>{title}</h1>" in resp.text
        assert "This is the" in resp.text

def test_404(fake_env):
    client = fake_env
    resp = client.get("/notfound")
    assert resp.status_code == 404
    assert "Not found" in resp.text
