import os
import sys

# Add backend directory to Python path for imports to work
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

try:
    from app.main import app
except Exception as e:
    import traceback
    error_trace = traceback.format_exc()
    print(f"Error importing app: {e}")
    # Create a dummy app to serve the error
    from fastapi import FastAPI, Response
    app = FastAPI()
    
    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
    async def catch_all(path_name: str):
        return Response(
            content=f"<h1>Backend Startup Error</h1><pre>{error_trace}</pre>", 
            media_type="text/html", 
            status_code=500
        )
