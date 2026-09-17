import asyncio
import json
from io import BytesIO

import httpx
import pytest
from PIL import Image
from pypdf import PdfWriter

from app import models
from app.extraction import receipts as provider
from app.routers import receipts
from tests.conftest import auth_headers, login


def image_bytes():
    output = BytesIO()
    Image.new('RGB', (60, 80), 'white').save(output, format='PNG')
    return output.getvalue()


def extracted():
    return {'receipt_detected': True, 'merchant': 'Sample Cafe', 'receipt_number': 'R-1',
            'date': '2026-09-17', 'currency': 'USD', 'subtotal': '10.00', 'tax': '1.00',
            'tip': None, 'discount': None, 'total': '11.00',
            'items': [{'description': 'Coffee', 'quantity': '2', 'unit_price': '5', 'amount': '10'}],
            'warnings': [], 'source_text': 'SAMPLE RECEIPT Coffee 10.00 Tax 1.00 Total USD 11.00'}


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setenv('INTERFAZE_ENABLED', 'true')
    monkeypatch.setenv('INTERFAZE_API_KEY', 'test-key-not-a-real-key')
    receipts._attempts.clear()
    yield
    receipts._attempts.clear()


def headers(client):
    return {**auth_headers(login(client, 'auditor', 'auditor123')),
            'Content-Type': 'image/png', 'X-Receipt-Consent': 'true'}


def test_requires_auth_and_explicit_consent(client, enabled):
    assert client.post('/receipts/extract', content=image_bytes()).status_code == 401
    auth = headers(client)
    del auth['X-Receipt-Consent']
    assert client.post('/receipts/extract', content=image_bytes(), headers=auth).status_code == 400


def test_disabled_service_does_not_contact_provider(client, monkeypatch):
    monkeypatch.delenv('INTERFAZE_ENABLED', raising=False)
    auth = headers(client)
    assert client.get('/receipts/status', headers=auth).json()['enabled'] is False
    assert client.post('/receipts/extract', content=image_bytes(), headers=auth).status_code == 503


def test_extraction_never_adds_uploads_to_shared_records(client, db_session, enabled, monkeypatch):
    async def fake(data, mime, key):
        assert data == image_bytes() and mime == 'image/png'
        return provider.ReceiptData.model_validate(extracted())
    monkeypatch.setattr(receipts, 'extract_receipt', fake)
    before = (db_session.query(models.Document).count(), db_session.query(models.AuditEvent).count())
    result = client.post('/receipts/extract', content=image_bytes(), headers=headers(client))
    assert result.status_code == 200, result.text
    assert result.json()['receipt']['total'] == '11.00'
    assert result.json()['stored_on_server'] is False
    assert len(result.json()['file_sha256']) == 64
    assert result.headers['cache-control'] == 'no-store'
    assert (db_session.query(models.Document).count(), db_session.query(models.AuditEvent).count()) == before
    assert client.get('/receipts', headers=headers(client)).status_code == 404


@pytest.mark.parametrize('data,mime,expected', [
    (b'', 'image/png', 400), (b'not an image', 'image/png', 400),
    (b'<svg/>', 'image/svg+xml', 415), (b'x' * (receipts.MAX_BYTES+1), 'image/png', 413),
    (b'%PDF-not valid', 'application/pdf', 400), (image_bytes(), 'image/jpeg', 400),
])
def test_invalid_files_rejected_before_provider(client, enabled, data, mime, expected):
    auth = {**headers(client), 'Content-Type': mime}
    assert client.post('/receipts/extract', content=data, headers=auth).status_code == expected


def test_pdf_page_limit_and_encryption():
    pdf = PdfWriter()
    for _ in range(4): pdf.add_blank_page(width=200, height=200)
    data = BytesIO(); pdf.write(data)
    with pytest.raises(Exception, match='1–3 pages'): receipts.validate_file(data.getvalue(), 'application/pdf')
    pdf = PdfWriter(); pdf.add_blank_page(width=200, height=200); pdf.encrypt('test')
    data = BytesIO(); pdf.write(data)
    with pytest.raises(Exception, match='password'): receipts.validate_file(data.getvalue(), 'application/pdf')


def test_provider_request_is_fixed_and_private(monkeypatch):
    client_class = httpx.AsyncClient
    def respond(request):
        assert str(request.url) == 'https://api.interfaze.ai/v1/chat/completions'
        assert request.headers['x-interfaze-zdr'] == 'true'
        assert request.headers['x-interfaze-bypass-cache'] == 'true'
        body = json.loads(request.content)
        assert body['model'] == 'interfaze'
        assert 'tools' not in body
        assert body['response_format']['type'] == 'json_schema'
        assert body['messages'][1]['content'][1]['image_url']['url'].startswith('data:image/png;base64,')
        return httpx.Response(200, json={'choices':[{'message':{'content':json.dumps(extracted())}}]})
    monkeypatch.setattr(provider.httpx, 'AsyncClient', lambda **kw: client_class(transport=httpx.MockTransport(respond), **kw))
    result = asyncio.run(provider.extract_receipt(image_bytes(), 'image/png', 'test'))
    assert str(result.total) == '11.00'


@pytest.mark.parametrize('code,expected', [(401,503),(403,503),(402,429),(429,429),(500,502)])
def test_provider_errors_do_not_leak_response_or_key(monkeypatch, code, expected):
    client_class = httpx.AsyncClient
    monkeypatch.setattr(provider.httpx, 'AsyncClient', lambda **kw: client_class(transport=httpx.MockTransport(lambda _:httpx.Response(code,text='private-provider-debug')), **kw))
    with pytest.raises(provider.ExtractionError) as error:
        asyncio.run(provider.extract_receipt(image_bytes(), 'image/png', 'test'))
    assert error.value.status == expected
    assert 'private-provider-debug' not in str(error.value)


def test_invalid_output_is_not_presented_as_extraction(monkeypatch):
    client_class = httpx.AsyncClient
    monkeypatch.setattr(provider.httpx, 'AsyncClient', lambda **kw: client_class(transport=httpx.MockTransport(lambda _:httpx.Response(200,json={'choices':[{'message':{'content':'{"total":"NaN"}'}}]})), **kw))
    with pytest.raises(provider.ExtractionError, match='incomplete'):
        asyncio.run(provider.extract_receipt(image_bytes(), 'image/png', 'test'))
