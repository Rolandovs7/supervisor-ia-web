from app.services import storage

URL = "https://res.cloudinary.com/demo/image/upload/supervisor-ia/a.png"


def test_upload_to_cloudinary_returns_secure_url(monkeypatch, tmp_path):
    configured = {}

    def fake_config(**kwargs):
        configured.update(kwargs)

    calls = {}

    def fake_upload(path, **kwargs):
        calls["path"] = path
        calls["kwargs"] = kwargs
        return {"secure_url": URL}

    monkeypatch.setattr(storage.cloudinary, "config", fake_config)
    monkeypatch.setattr(storage.cloudinary.uploader, "upload", fake_upload)
    monkeypatch.setattr(storage.settings, "cloudinary_url", "")
    monkeypatch.setattr(storage.settings, "cloudinary_cloud_name", "demo")
    monkeypatch.setattr(storage.settings, "cloudinary_api_key", "key")
    monkeypatch.setattr(storage.settings, "cloudinary_api_secret", "secret")

    image = tmp_path / "a.png"
    image.write_bytes(b"fake")

    assert storage.upload_to_cloudinary(image) == URL
    assert configured["cloud_name"] == "demo"
    assert configured["secure"] is True
    assert calls["path"] == str(image)
    assert calls["kwargs"]["resource_type"] == "image"
