import os
import tempfile
import shutil
import pytest
from starlette.testclient import TestClient
from zbricks.docs.serve import create_app

def make_fake_docs(tmp_path):
    content_dir = tmp_path / "content"
    theme_dir = tmp_path / "theme"
    content_dir.mkdir()
    theme_dir.mkdir()
    (content_dir / "example1.md").write_text(
        """---\ntitle: Example 1\nslug: example1\n---\n\n# Example 1\n\nThis is the first example document.\n"""
    )
    (content_dir / "example2.md").write_text(
        """---\ntitle: Example 2\nslug: example2\n---\n\n# Example 2\n\nThis is the second example document.\n"""
    )
    # Minimal theme with required templates
    (theme_dir / "base.html").write_text(
        """<!DOCTYPE html><html><head><title>{% block title %}Docs{% endblock %}</title></head><body>{% block content %}{% endblock %}</body></html>"""
    )
    (theme_dir / "index.html").write_text(
        """{% extends 'base.html' %}{% block content %}<ul>{% for doc in docs %}<li><a href='/{{ doc.slug }}'>{{ doc.title }}</a></li>{% endfor %}</ul>{% endblock %}"""
    )
    (theme_dir / "doc.html").write_text(
        """{% extends 'base.html' %}{% block title %}{{ doc.title }}{% endblock %}{% block content %}<h1>{{ doc.title }}</h1>{{ content|safe }}{% endblock %}"""
    )
    return str(content_dir), str(theme_dir)

@pytest.fixture
def fake_env(tmp_path):
    content_dir, theme_dir = make_fake_docs(tmp_path)
    app = create_app(content_dir, theme_dir)
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
        assert f"This is the" in resp.text

def test_404(fake_env):
    client = fake_env
    resp = client.get("/notfound")
    assert resp.status_code == 404
    assert "Not found" in resp.text
