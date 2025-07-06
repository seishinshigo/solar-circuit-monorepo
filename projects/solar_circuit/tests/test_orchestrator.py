from httpx import ASGITransport, AsyncClient
from solar_circuit.orchestrator.main import app
import pytest

@pytest.mark.asyncio
async def test_health_check():
    """ヘルスチェックエンドポイントが正しく動作することを確認する。"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
