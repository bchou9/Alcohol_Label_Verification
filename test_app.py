import types

import app


class DummyUploadedFile:
    def __init__(self, data: bytes, mime_type: str = "image/png", name: str = "label.png"):
        self._data = data
        self.type = mime_type
        self.name = name

    def getvalue(self):
        return self._data


def test_government_warning_requires_exact_caps_and_statutory_text():
    valid = (
        "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy "
        "because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car "
        "or operate machinery, and may cause health problems."
    )

    assert app.has_valid_government_warning(valid)
    assert not app.has_valid_government_warning(valid.replace("GOVERNMENT WARNING:", "Government Warning:"))


def test_brand_matching_is_case_and_token_order_tolerant():
    assert app.nuanced_brand_match("Stone's Throw", "STONE'S THROW")
    assert app.nuanced_brand_match("Old Tom Distillery", "Distillery Old Tom")
    assert not app.nuanced_brand_match("Old Tom Distillery", "Completely Different Brand")


def test_abv_matching_handles_percent_and_proof_forms():
    assert app.abv_matches("45%", "45.0%")
    assert app.abv_matches("45%", "90 Proof")
    assert not app.abv_matches("45%", "40%")


def test_analyze_label_with_ai_uses_byte_payload_and_strict_schema(monkeypatch):
    calls = {}

    def fake_from_bytes(*, data, mime_type):
        calls["from_bytes"] = (data, mime_type)
        return {"part": True}

    class FakeModels:
        def generate_content(self, *, model, contents, config):
            calls["model"] = model
            calls["contents"] = contents
            calls["config"] = config
            return types.SimpleNamespace(
                parsed={"brand": "OLD TOM DISTILLERY", "abv": "45%", "raw_text": "GOVERNMENT WARNING: ..."},
                text="unused",
            )

    class FakeClient:
        def __init__(self, api_key):
            calls["api_key"] = api_key
            self.models = FakeModels()

    monkeypatch.setattr(app.types.Part, "from_bytes", fake_from_bytes)
    monkeypatch.setattr(app.genai, "Client", FakeClient)
    monkeypatch.setattr(app, "api_key", "unit-test-key")

    result = app.analyze_label_with_ai(DummyUploadedFile(b"binary-image", "image/png"), "label.png")

    assert result == {"brand": "OLD TOM DISTILLERY", "abv": "45%", "raw_text": "GOVERNMENT WARNING: ..."}
    assert calls["api_key"] == "unit-test-key"
    assert calls["from_bytes"] == (b"binary-image", "image/png")
    assert calls["model"] == "gemini-2.5-flash"

    schema = calls["config"].response_schema
    assert calls["config"].response_mime_type == "application/json"
    assert getattr(schema, "type") == app.types.Type.OBJECT
    assert set(schema.properties.keys()) == {"brand", "abv", "raw_text"}
    assert schema.required == ["brand", "abv", "raw_text"]


def test_analyze_label_with_ai_rejects_non_dict_schema_results(monkeypatch):
    class FakeModels:
        def generate_content(self, *, model, contents, config):
            return types.SimpleNamespace(parsed=[1, 2, 3], text='[1, 2, 3]')

    class FakeClient:
        def __init__(self, api_key):
            self.models = FakeModels()

    monkeypatch.setattr(app.genai, "Client", FakeClient)
    monkeypatch.setattr(app, "api_key", "unit-test-key")

    result = app.analyze_label_with_ai(DummyUploadedFile(b"binary-image"), "label.png")
    assert "error" in result
