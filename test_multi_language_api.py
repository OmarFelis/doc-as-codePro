"""Test API with multi-language project."""
import asyncio
import httpx


async def test_multi_language_analysis():
    """Test analyzing a project with multiple languages."""
    
    base_url = "http://127.0.0.1:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        health_response = await client.get(f"{base_url}/health")
        print(f"✅ Health: {health_response.json()}\n")
        
        # Start analysis
        print("🚀 Starting analysis of current project...")
        analysis_request = {
            "local_path": "C:/Users/ocardenas/OneDrive - BIZLINKS SAC/Documentos/doc-as-codePRO",
            "languages": ["python", "java", "javascript", "typescript"],
            "options": {
                "generate_docs": False,
                "cache_enabled": False
            }
        }
        
        create_response = await client.post(
            f"{base_url}/analyze",
            json=analysis_request
        )
        
        if create_response.status_code != 200:
            print(f"❌ Error: {create_response.status_code}")
            print(create_response.text)
            return
        
        result = create_response.json()
        analysis_id = result["analysis_id"]
        print(f"📝 Analysis ID: {analysis_id}")
        print(f"📊 Status: {result['status']}\n")
        
        # Poll for results
        print("⏳ Waiting for analysis to complete...")
        for i in range(30):  # Max 30 seconds
            await asyncio.sleep(1)
            
            status_response = await client.get(f"{base_url}/analysis/{analysis_id}")
            status_data = status_response.json()
            
            print(f"  Progress: {status_data.get('progress', 0)}% - {status_data.get('current_step', 'Processing')}")
            
            if status_data["status"] == "completed":
                print("\n✅ Analysis completed!")
                print(f"\n📊 Results:")
                print(f"  - Repository: {status_data.get('repository_name')}")
                print(f"  - Total Files: {status_data.get('total_files')}")
                print(f"  - Total Lines: {status_data.get('total_lines'):,}")
                print(f"  - Languages: {', '.join(status_data.get('languages', []))}")
                print(f"\n🏗️  Components:")
                for comp_type, count in status_data.get('components', {}).items():
                    print(f"  - {comp_type.upper()}: {count} files")
                break
            elif status_data["status"] == "failed":
                print(f"\n❌ Analysis failed: {status_data.get('error')}")
                break


if __name__ == "__main__":
    asyncio.run(test_multi_language_analysis())
