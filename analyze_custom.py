"""
Interactive API test - Analyze any project you want!

This script allows you to analyze any local project directory.
"""

import asyncio
import httpx
from pathlib import Path


async def analyze_project(project_path: str):
    """Analyze a specific project."""
    base_url = "http://localhost:8000"
    
    print("=" * 70)
    print(f"  Analyzing: {project_path}")
    print("=" * 70)
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create analysis request
        print("[1/3] Creating analysis request...")
        analysis_request = {
            "local_path": project_path,
            "branch": "main",
            "languages": None  # Auto-detect all languages
        }
        
        try:
            response = await client.post(
                f"{base_url}/api/v1/analyze",
                json=analysis_request
            )
            
            if response.status_code != 202:
                print(f"[ERROR] Failed to create analysis: {response.status_code}")
                print(f"Response: {response.text}")
                return
            
            response_data = response.json()
            analysis_id = response_data["analysis_id"]
            print(f"    Analysis ID: {analysis_id}")
            print(f"    Status: {response_data['status']}\n")
            
            # Wait for analysis to complete
            print("[2/3] Waiting for analysis to complete...")
            max_attempts = 10
            attempt = 0
            
            while attempt < max_attempts:
                await asyncio.sleep(2)
                attempt += 1
                
                response = await client.get(
                    f"{base_url}/api/v1/analysis/{analysis_id}"
                )
                result = response.json()
                
                status = result['status']
                progress = result.get('progress', 0)
                print(f"    Attempt {attempt}: Status={status}, Progress={progress}%")
                
                if status == 'completed':
                    break
                elif status == 'failed':
                    print(f"[ERROR] Analysis failed: {result.get('error')}")
                    return
            
            # Display results
            print("\n[3/3] Analysis Results:")
            print("-" * 70)
            print(f"Repository: {result.get('repository_name', 'N/A')}")
            print(f"Total Files: {result.get('total_files', 0)}")
            print(f"Total Lines: {result.get('total_lines', 0):,}")
            print(f"Languages: {', '.join(result.get('languages', []))}")
            print()
            print("Components by Type:")
            components = result.get('components', {})
            if components:
                for comp_type, count in components.items():
                    print(f"  - {comp_type}: {count} files")
            else:
                print("  (No components detected)")
            print()
            print(f"Status: {result['status']}")
            print(f"Created: {result['created_at']}")
            print(f"Completed: {result.get('completed_at', 'N/A')}")
            print("-" * 70)
            print()
            print("[OK] Analysis completed successfully!")
            
        except httpx.ConnectError:
            print("[ERROR] Cannot connect to API!")
            print("Make sure the API is running:")
            print("  poetry run python src/api/main.py")
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            print()
            import traceback
            print("Full traceback:")
            traceback.print_exc()


def main():
    """Main entry point."""
    print()
    print("=" * 70)
    print("  DOC-AS-CODE API - Custom Project Analysis")
    print("=" * 70)
    print()
    print("Enter the path to the project you want to analyze.")
    print("Examples:")
    print("  .                           (current directory)")
    print("  C:\\MyProjects\\my-app       (absolute path)")
    print("  ../another-project          (relative path)")
    print()
    
    project_path = input("Project path: ").strip()
    
    if not project_path:
        print("[ERROR] No path provided!")
        return
    
    # Validate path exists
    path = Path(project_path)
    if not path.exists():
        print(f"[ERROR] Path does not exist: {project_path}")
        return
    
    if not path.is_dir():
        print(f"[ERROR] Path is not a directory: {project_path}")
        return
    
    print()
    asyncio.run(analyze_project(project_path))


if __name__ == "__main__":
    main()
