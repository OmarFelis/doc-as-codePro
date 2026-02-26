"""
Quick test script for the API.

Run this to test the API endpoints locally.
"""

import asyncio
import httpx
from pathlib import Path


async def test_api():
    """Test API endpoints."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Test root endpoint
        print("[*] Testing root endpoint...")
        response = await client.get(f"{base_url}/")
        print(f"    Status: {response.status_code}")
        print(f"    Response: {response.json()}\n")
        
        # Test health endpoint
        print("[*] Testing health endpoint...")
        response = await client.get(f"{base_url}/health")
        print(f"    Status: {response.status_code}")
        print(f"    Response: {response.json()}\n")
        
        # Test analysis endpoint
        print("[*] Creating analysis request...")
        analysis_request = {
            "local_path": ".",  # Analyze current project
            "branch": "main",
            "languages": ["python"]
        }
        response = await client.post(
            f"{base_url}/api/v1/analyze",
            json=analysis_request
        )
        print(f"    Status: {response.status_code}")
        response_data = response.json()
        print(f"    Response: {response_data}\n")
        
        if response.status_code == 202:
            analysis_id = response_data["analysis_id"]
            
            # Wait a bit for analysis to process
            print("[*] Waiting for analysis to complete...")
            await asyncio.sleep(3)
            
            # Get analysis result
            print(f"[*] Getting analysis result for {analysis_id}...")
            response = await client.get(f"{base_url}/api/v1/analysis/{analysis_id}")
            print(f"    Status: {response.status_code}")
            result = response.json()
            print(f"    Status: {result['status']}")
            print(f"    Files: {result.get('total_files', 'N/A')}")
            print(f"    Lines: {result.get('total_lines', 'N/A')}")
            print(f"    Languages: {result.get('languages', [])}")
            print(f"    Components: {result.get('components', {})}\n")
        
        print("[OK] API tests completed!")


if __name__ == "__main__":
    print("=" * 60)
    print("  DOC-AS-CODE API - Quick Test")
    print("=" * 60)
    print()
    asyncio.run(test_api())
