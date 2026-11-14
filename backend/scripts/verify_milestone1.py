import os
import sys
# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import httpx
from app.main import app

async def main():
    print("Testing Milestone 1 API Endpoints...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Root endpoint
        r1 = await client.get("/")
        assert r1.status_code == 200, f"Expected 200 got {r1.status_code}"
        d1 = r1.json()
        print("✓ Root endpoint:", d1)
        assert "version" in d1

        # 2. Top-level health
        r2 = await client.get("/health")
        assert r2.status_code == 200, f"Expected 200 got {r2.status_code}"
        d2 = r2.json()
        print("✓ Health endpoint:", d2)
        assert d2["status"] == "healthy"

        # 3. API v1 health
        r3 = await client.get("/api/v1/health")
        assert r3.status_code == 200, f"Expected 200 got {r3.status_code}"
        d3 = r3.json()
        print("✓ API v1 Health endpoint:", d3)
        assert d3["status"] == "healthy"

    print("\nALL MILESTONE 1 API CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(main())
