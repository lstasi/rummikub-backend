#!/usr/bin/env python3
"""
Script to generate and save OpenAPI specification for the Rummikub Backend API.

This script imports the FastAPI application and generates a static OpenAPI JSON file
that can be version controlled and used independently of running the server.
"""

import sys
import os
import json

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import app


def generate_openapi_spec():
    """Generate OpenAPI specification and save to file."""
    
    # Get the OpenAPI schema from the FastAPI app
    openapi_schema = app.openapi()
    
    # Pretty format the JSON
    formatted_json = json.dumps(openapi_schema, indent=2, sort_keys=True)
    
    # Save to file in project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    openapi_path = os.path.join(project_root, "openapi.json")
    
    with open(openapi_path, "w", encoding="utf-8") as f:
        f.write(formatted_json)
    
    print("✅ OpenAPI specification generated successfully!")
    print(f"📁 Saved to: {openapi_path}")
    print(f"📊 API Title: {openapi_schema.get('info', {}).get('title', 'N/A')}")
    print(f"🔢 API Version: {openapi_schema.get('info', {}).get('version', 'N/A')}")
    print(f"🛠️  OpenAPI Version: {openapi_schema.get('openapi', 'N/A')}")
    print(f"🎯 Total Endpoints: {len(openapi_schema.get('paths', {}))}")
    
    # Print endpoint summary
    paths = openapi_schema.get('paths', {})
    print("\n📋 Available Endpoints:")
    for path, methods in paths.items():
        for method, details in methods.items():
            summary = details.get('summary', 'No summary')
            print(f"   {method.upper():6} {path:30} - {summary}")


if __name__ == "__main__":
    generate_openapi_spec()