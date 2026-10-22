import httpx


class OrdersClient:
    """Calls the orders service over its internal address. Never a public URL."""

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def create_order(self, payload: dict[str, object], request_id: str) -> httpx.Response:
        return await self._http.post("/orders", json=payload, headers={"X-Request-ID": request_id})

    async def get_order(self, order_id: str, request_id: str) -> httpx.Response:
        return await self._http.get(f"/orders/{order_id}", headers={"X-Request-ID": request_id})
