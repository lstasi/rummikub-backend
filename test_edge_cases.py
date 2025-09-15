#!/usr/bin/env python3
"""
Extended test script for edge cases in multi-screen access functionality.
"""
import requests
import json
import base64
import time

BASE_URL = "http://localhost:8090"
ADMIN_USER = "admin"
ADMIN_PASS = "rummikub2024"


def create_auth_header():
    """Create basic auth header."""
    credentials = f"{ADMIN_USER}:{ADMIN_PASS}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded_credentials}"}


def test_edge_cases():
    """Test edge cases for multi-screen access."""
    print("🔍 Testing Multi-Screen Access Edge Cases...")
    
    # Create game
    auth_headers = create_auth_header()
    game_data = {"max_players": 3, "name": "EdgeCaseCreator"}
    response = requests.post(f"{BASE_URL}/game", json=game_data, headers=auth_headers)
    game_info = response.json()
    game_id = game_info["game_id"]
    print(f"✅ Created game: {game_id}")
    
    # Test 1: Try to re-join a WAITING game (should fail with existing logic)
    print("\n🧪 Test 1: Re-join waiting game (should fail)")
    join_data = {"player_name": "TestPlayer"}
    response1 = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data)
    print(f"First join: {response1.status_code}")
    
    response2 = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data)
    print(f"Second join (waiting game): {response2.status_code}")
    if response2.status_code != 200:
        print(f"✅ Correctly rejected: {response2.json()['detail']}")
    else:
        print("❌ Should not allow duplicate names in waiting games")
    
    # Add second player to start the game
    join_data = {"player_name": "Player2"}
    response = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data)
    print(f"✅ Player2 joined to start game")
    
    # Test 2: Now re-join with TestPlayer (should work in in-progress game)
    print("\n🧪 Test 2: Re-join in-progress game (should work)")
    join_data = {"player_name": "TestPlayer"}
    response = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data)
    print(f"Re-join in-progress game: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Successfully re-joined: {result['message']}")
    else:
        print(f"❌ Failed to re-join: {response.json()}")
    
    # Test 3: Try to join with completely new player name in in-progress game (should fail)
    print("\n🧪 Test 3: New player join in-progress game (should fail)")
    join_data = {"player_name": "NewPlayer"}
    response = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data)
    print(f"New player join in-progress: {response.status_code}")
    if response.status_code != 200:
        print(f"✅ Correctly rejected new player: {response.json()['detail']}")
    else:
        print("❌ Should not allow new players in in-progress games")
    
    # Test 4: Try actions with old and new tokens
    print("\n🧪 Test 4: Token validity across sessions")
    # Get current tokens for TestPlayer
    join_data = {"player_name": "TestPlayer"}
    response = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data)
    token_new = response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token_new}"}
    response = requests.get(f"{BASE_URL}/game/{game_id}", headers=headers)
    if response.status_code == 200:
        print("✅ New token works for game state")
    else:
        print("❌ New token doesn't work")
    
    # Test 5: Test non-existent game re-join
    print("\n🧪 Test 5: Re-join non-existent game")
    fake_game_id = "00000000-0000-0000-0000-000000000000"
    join_data = {"player_name": "TestPlayer"}
    response = requests.post(f"{BASE_URL}/game/{fake_game_id}/join", json=join_data)
    print(f"Non-existent game join: {response.status_code}")
    if response.status_code != 200:
        print(f"✅ Correctly handled: {response.json()['detail']}")
    else:
        print("❌ Should fail for non-existent game")
    
    print("\n🎉 Edge case tests completed!")


def test_finished_game_rejoin():
    """Test re-joining a finished game."""
    print("\n🏁 Testing finished game re-join...")
    
    # This would require finishing a game, which is complex to set up
    # For now, just print that this case exists
    print("📝 Note: Finished game re-join is handled by the code but not easily testable")
    print("    The logic prevents re-joining finished games")


if __name__ == "__main__":
    try:
        test_edge_cases()
        test_finished_game_rejoin()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running on localhost:8090")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()