#!/usr/bin/env python3
"""
Test script to validate the generated OpenAPI specification.
"""

import json
import os
import sys


def validate_openapi_file():
    """Validate the OpenAPI specification file."""
    
    openapi_file = "openapi.json"
    
    # Check if file exists
    if not os.path.exists(openapi_file):
        print(f"❌ Error: {openapi_file} not found!")
        return False
    
    # Load and validate JSON
    try:
        with open(openapi_file, 'r', encoding='utf-8') as f:
            spec = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {openapi_file}: {e}")
        return False
    
    # Validate required OpenAPI fields
    required_fields = ["openapi", "info", "paths"]
    for field in required_fields:
        if field not in spec:
            print(f"❌ Error: Missing required field '{field}' in OpenAPI spec")
            return False
    
    # Validate OpenAPI version
    if not spec["openapi"].startswith("3."):
        print(f"❌ Error: Expected OpenAPI 3.x, got {spec['openapi']}")
        return False
    
    # Validate info section
    info = spec["info"]
    if not info.get("title") or not info.get("version"):
        print("❌ Error: Missing title or version in info section")
        return False
    
    # Validate paths
    paths = spec["paths"]
    expected_paths = ["/", "/game", "/game/{game_id}/join", "/game/{game_id}", 
                      "/game/{game_id}/action", "/game/{game_id}/info"]
    
    for expected_path in expected_paths:
        if expected_path not in paths:
            print(f"❌ Error: Missing expected path '{expected_path}'")
            return False
    
    # Validate tags
    tags = spec.get("tags", [])
    expected_tags = ["general", "game-management", "game-play"]
    tag_names = [tag["name"] for tag in tags]
    
    for expected_tag in expected_tags:
        if expected_tag not in tag_names:
            print(f"❌ Error: Missing expected tag '{expected_tag}'")
            return False
    
    # Print success info
    print("✅ OpenAPI specification validation passed!")
    print(f"📊 Title: {info['title']}")
    print(f"🔢 Version: {info['version']}")
    print(f"🛠️  OpenAPI Version: {spec['openapi']}")
    print(f"🎯 Paths: {len(paths)}")
    print(f"🏷️  Tags: {len(tags)}")
    
    return True


if __name__ == "__main__":
    success = validate_openapi_file()
    sys.exit(0 if success else 1)