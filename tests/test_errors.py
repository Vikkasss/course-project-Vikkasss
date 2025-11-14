from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_not_found_item():
    r = client.get("/items/999")
    assert r.status_code == 404
    body = r.json()
    assert "detail" in body and body["detail"] == "Item not found"
    assert "title" in body and body["title"] == "Not Found"


def test_validation_error():
    r = client.post("/items", params={"name": ""})
    assert r.status_code == 422
    body = r.json()
    assert (
        "detail" in body
        and "Name must be between 1 and 100 characters" in body["detail"]
    )
    assert "title" in body and body["title"] == "Validation Failed"


def test_get_quotes_empty():
    r = client.get("/quotes")
    assert r.status_code == 200
    assert r.json() == []


def test_create_quote():
    quote = {
        "text": "Example quote",
        "author": "Example author",
        "book": "Example book",
    }
    r = client.post("/quotes", json=quote)
    assert r.status_code == 200
    response_data = r.json()
    assert response_data["text"] == quote["text"]
    assert response_data["author"] == quote["author"]
    assert response_data["book"] == quote["book"]
    assert "id" in response_data
    assert "created_date" in response_data


def test_get_quote_by_id():
    quote = {
        "text": "Example quote",
        "author": "Example author",
        "book": "Example book",
    }
    create_response = client.post("/quotes", json=quote)
    quote_id = create_response.json()["id"]
    r = client.get(f"/quotes/{quote_id}")
    assert r.status_code == 200
    response_data = r.json()
    assert response_data["id"] == quote_id
    assert response_data["text"] == quote["text"]


def test_get_quote_by_id_not_found():
    r = client.get("/quotes/999")
    assert r.status_code == 404
    body = r.json()
    assert "detail" in body and body["detail"] == "Quote not found"
    assert "title" in body and body["title"] == "Not Found"


def test_get_quotes_by_book():
    quote1 = {"text": "Quote 1", "author": "Author 1", "book": "Book A"}

    quote2 = {"text": "Quote 2", "author": "Author 2", "book": "Book A"}

    quote3 = {"text": "Quote 3", "author": "Author 3", "book": "Book B"}

    client.post("/quotes", json=quote1)
    client.post("/quotes", json=quote2)
    client.post("/quotes", json=quote3)

    r = client.get("/quotes/book/Book%20A")
    assert r.status_code == 200
    quotes = r.json()
    assert len(quotes) == 2
    assert all(quote["book"] == "Book A" for quote in quotes)


def test_delete_quote():
    quote = {"text": "Quote 1", "author": "Author 1", "book": "Book A"}
    create_response = client.post("/quotes", json=quote)
    quote_id = create_response.json()["id"]

    r = client.get(f"/quotes/{quote_id}")
    assert r.status_code == 200

    delete_response = client.delete(f"/quotes/{quote_id}")
    assert delete_response.status_code == 200
    delete_data = delete_response.json()
    assert delete_data["message"] == "Quote deleted"
    r = client.get(f"/quotes/{quote_id}")
    assert r.status_code == 404
