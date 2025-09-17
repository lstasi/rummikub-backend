#!/usr/bin/env python3
"""
Test script to verify environment variable override functionality for admin password.
"""
import requests
import json
import base64
import os
import subprocess
import time
import signal
import sys

BASE_URL = "http://localhost:8090"
ADMIN_USER = "admin"
DEFAULT_PASS = "admin"
CUSTOM_PASS = "custom_test_password_123"


def create_auth_header(password):
    """Create basic auth header with specified password."""
    credentials = f"{ADMIN_USER}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded_credentials}"}


def test_game_creation_with_password(password, should_succeed=True):
    """Test game creation with a specific password."""
    auth_headers = create_auth_header(password)
    game_data = {"max_players": 2, "name": "TestCreator"}
    
    try:
        response = requests.post(f"{BASE_URL}/game", json=game_data, headers=auth_headers)
        if should_succeed:
            if response.status_code == 200:
                print(f"✅ Authentication successful with password: {password}")
                return True
            else:
                print(f"❌ Authentication failed with password: {password} (expected success)")
                print(f"Status: {response.status_code}, Response: {response.json()}")
                return False
        else:
            if response.status_code == 401:
                print(f"✅ Authentication correctly rejected with password: {password}")
                return True
            else:
                print(f"❌ Authentication unexpectedly succeeded with password: {password}")
                return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False


def start_server_with_env_password(custom_password=None):
    """Start server with optional custom password environment variable."""
    env = os.environ.copy()
    if custom_password:
        env["ADMIN_PASSWORD"] = custom_password
    else:
        # Remove the env var to test default behavior
        env.pop("ADMIN_PASSWORD", None)
    
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd="/home/runner/work/rummikub-backend/rummikub-backend",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    # Wait for server to start
    time.sleep(3)
    return process


def test_env_password_functionality():
    """Test that password can be overridden by environment variable."""
    print("🔐 Testing Environment Variable Password Override...")
    
    # Test 1: Default password behavior (no env var)
    print("\n1. Testing default password behavior...")
    server_process = start_server_with_env_password()
    
    try:
        # Should succeed with default password
        success = test_game_creation_with_password(DEFAULT_PASS, should_succeed=True)
        if not success:
            return False
        
        # Should fail with custom password
        success = test_game_creation_with_password(CUSTOM_PASS, should_succeed=False)
        if not success:
            return False
    finally:
        server_process.terminate()
        server_process.wait()
    
    time.sleep(1)
    
    # Test 2: Custom password behavior (with env var)
    print("\n2. Testing custom password via environment variable...")
    server_process = start_server_with_env_password(CUSTOM_PASS)
    
    try:
        # Should fail with default password
        success = test_game_creation_with_password(DEFAULT_PASS, should_succeed=False)
        if not success:
            return False
        
        # Should succeed with custom password
        success = test_game_creation_with_password(CUSTOM_PASS, should_succeed=True)
        if not success:
            return False
    finally:
        server_process.terminate()
        server_process.wait()
    
    return True


if __name__ == "__main__":
    if test_env_password_functionality():
        print("\n🎉 Environment variable password override functionality working correctly!")
    else:
        print("\n❌ Environment variable password override functionality failed!")
        sys.exit(1)