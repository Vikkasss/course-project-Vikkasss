import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestInputValidation:
    def test_quote_validation_empty_fields(self):
        quote = {"text": "   ", "author": "  ", "book": "  "}
        r = client.post("/quotes", json=quote)
        assert r.status_code == 422

    def test_quote_validation_extra_fields(self):
        quote = {
            "text": "Valid text",
            "author": "Valid author",
            "book": "Valid book",
            "malicious_field": "hack",
        }
        r = client.post("/quotes", json=quote)
        assert r.status_code == 422

    def test_quote_validation_max_length(self):
        long_text = "x" * 2001
        quote = {"text": long_text, "author": "Author", "book": "Book"}
        r = client.post("/quotes", json=quote)
        assert r.status_code == 422


class TestErrorFormat:

    def test_problem_detail_format(self):
        r = client.get("/items/9999")
        assert r.status_code == 404
        body = r.json()

        assert "type" in body
        assert "title" in body
        assert "status" in body
        assert "detail" in body
        assert "correlation_id" in body
        assert "instance" in body

        assert body["status"] == 404
        assert body["title"] == "Not Found"

    def test_validation_error_format(self):
        r = client.post("/items", params={"name": ""})
        assert r.status_code == 422
        body = r.json()
        assert body["type"] == "/errors/validation"


class TestFileSecurity:

    def test_upload_large_file(self):
        large_file = io.BytesIO(b"x" * (10_000_000 + 1))
        files = {"file": ("large.jpg", large_file, "image/jpeg")}
        r = client.post("/upload-cover", files=files)
        assert r.status_code == 413

    def test_upload_invalid_file_type(self):
        fake_jpg = io.BytesIO(b"fake content")
        files = {"file": ("fake.jpg", fake_jpg, "image/jpeg")}
        r = client.post("/upload-cover", files=files)
        assert r.status_code == 415

    def test_upload_valid_file(self):
        # Минимальный валидный JPEG
        valid_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\x09\x09\x08\x0a\x0c\x14\x0d\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $. ' \"#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\x09\n\x16\x17\x18\x19\x1a%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xff\xd9"
        files = {"file": ("valid.jpg", io.BytesIO(valid_jpeg), "image/jpeg")}
        r = client.post("/upload-cover", files=files)
        assert r.status_code == 200


class TestSQLInjectionProtection:
    def test_sql_injection_attempt(self):
        malicious_book = "Book' OR '1'='1"
        r = client.get(f"/quotes/book/{malicious_book}")
        assert r.status_code in [404, 200]  # 404 если нет книг, 200 если есть
        assert r.status_code != 500
