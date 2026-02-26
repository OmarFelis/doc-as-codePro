"""
Debug script - Run this to analyze with detailed error messages
"""

import asyncio
import httpx
import sys


async def debug_analyze(project_path: str):
    """Analyze with detailed debugging."""
    base_url = "http://localhost:8000"
    
    print(f"[DEBUG] Analyzing: {project_path}")
    print(f"[DEBUG] API URL: {base_url}")
    print()
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Step 1: Create analysis
            print("[1] Creating analysis request...")
            analysis_request = {
                "local_path": project_path,
                "branch": "main",
                "languages": None
            }
            
            print(f"[DEBUG] Request body: {analysis_request}")
            
            response = await client.post(
                f"{base_url}/api/v1/analyze",
                json=analysis_request
            )
            
            print(f"[DEBUG] Response status: {response.status_code}")
            print(f"[DEBUG] Response headers: {dict(response.headers)}")
            
            if response.status_code != 202:
                print(f"[ERROR] Unexpected status code!")
                print(f"Response body: {response.text}")
                return
            
            data = response.json()
            analysis_id = data["analysis_id"]
            print(f"[OK] Analysis created: {analysis_id}")
            print()
            
            # Step 2: Poll for results
            print("[2] Polling for results...")
            for attempt in range(20):
                await asyncio.sleep(2)
                
                print(f"[DEBUG] Attempt {attempt + 1}/20")
                
                try:
                    response = await client.get(
                        f"{base_url}/api/v1/analysis/{analysis_id}"
                    )
                    
                    print(f"[DEBUG] Status code: {response.status_code}")
                    
                    if response.status_code != 200:
                        print(f"[ERROR] Get analysis failed: {response.text}")
                        continue
                    
                    result = response.json()
                    status = result.get('status')
                    error = result.get('error')
                    
                    print(f"[DEBUG] Analysis status: {status}")
                    
                    if error:
                        print(f"[ERROR] Analysis error: {error}")
                        return
                    
                    if status == 'completed':
                        print()
                        print("[OK] Analysis completed!")
                        print(f"Files: {result.get('total_files')}")
                        print(f"Lines: {result.get('total_lines')}")
                        print(f"Languages: {result.get('languages')}")
                        print(f"Components: {result.get('components')}")
                        return
                    
                    elif status == 'failed':
                        print(f"[ERROR] Analysis failed!")
                        print(f"Error: {result.get('error', 'Unknown error')}")
                        return
                    
                except Exception as e:
                    print(f"[ERROR] Exception during polling: {e}")
                    import traceback
                    traceback.print_exc()
                    return
            
            print("[WARN] Analysis timed out after 20 attempts")
            
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = input("Project path: ").strip()
    
    print("=" * 70)
    print("  DEBUG MODE - Detailed Error Messages")
    print("=" * 70)
    print()
    
    asyncio.run(debug_analyze(project_path))
