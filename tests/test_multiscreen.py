#!/usr/bin/env python3
"""
Test script for multi-screen access functionality.
Tests that multiple sessions can be created for the same player and handles concurrent actions.
"""
import requests
import json
import base64
import time
import threading
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:8090"
ADMIN_USER = "admin"
ADMIN_PASS = "admin"


def create_auth_header():
    """Create basic auth header."""
    credentials = f"{ADMIN_USER}:{ADMIN_PASS}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded_credentials}"}


def test_multiscreen_access():
    """Test multi-screen access functionality."""
    print("🎯 Testing Multi-Screen Access...")
    
    # Create game
    auth_headers = create_auth_header()
    game_data = {"max_players": 2, "name": "MultiScreenTestCreator"}
    response = requests.post(f"{BASE_URL}/game", json=game_data, headers=auth_headers)
    game_info = response.json()
    game_id = game_info["game_id"]
    print(f"✅ Created game: {game_id}")
    
    # Join game with Player1 - first session
    join_data = {"player_name": "Player1"}
    response = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data)
    player1_session1 = response.json()
    token1_session1 = player1_session1["access_token"]
    print(f"✅ Player1 joined (Session 1)")
    
    # Join game with Player2 to start the game
    join_data = {"player_name": "Player2"}
    response = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data)
    player2_info = response.json()
    token2 = player2_info["access_token"]
    print(f"✅ Player2 joined - Game should now be in progress")
    
    # Now try to join again with Player1 - should create a second session
    print("\n🔄 Testing re-join for multi-screen access...")
    join_data = {"player_name": "Player1"}
    response = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data)
    
    if response.status_code == 200:
        player1_session2 = response.json()
        token1_session2 = player1_session2["access_token"]
        print(f"✅ Player1 re-joined successfully (Session 2)")
        print(f"Message: {player1_session2['message']}")
        
        # Verify tokens are different (unique sessions)
        if token1_session1 != token1_session2:
            print("✅ Sessions have different tokens (multi-screen support confirmed)")
        else:
            print("❌ Tokens are identical - sessions not properly separated")
            
    else:
        print(f"❌ Failed to re-join: {response.status_code} - {response.json()}")
        return
    
    # Test that both sessions can view game state
    print("\n📊 Testing game state access from multiple sessions...")
    
    headers1_s1 = {"Authorization": f"Bearer {token1_session1}"}
    headers1_s2 = {"Authorization": f"Bearer {token1_session2}"}
    
    response1 = requests.get(f"{BASE_URL}/game/{game_id}", headers=headers1_s1)
    response2 = requests.get(f"{BASE_URL}/game/{game_id}", headers=headers1_s2)
    
    if response1.status_code == 200 and response2.status_code == 200:
        game_state1 = response1.json()
        game_state2 = response2.json()
        
        print(f"✅ Both sessions can access game state")
        print(f"Session 1 sees {len(game_state1['your_tiles'])} tiles")
        print(f"Session 2 sees {len(game_state2['your_tiles'])} tiles")
        print(f"Current player: {game_state1['current_player']}")
        print(f"Can play (both sessions): {game_state1['can_play']}")
        
        # Verify both sessions see the same game state (same player)
        if (len(game_state1['your_tiles']) == len(game_state2['your_tiles']) and 
            game_state1['current_player'] == game_state2['current_player']):
            print("✅ Both sessions show identical game state for the same player")
        else:
            print("❌ Sessions show different game states")
    else:
        print("❌ Failed to get game state from one or both sessions")
        return
    
    # Test concurrent actions (first one should win)
    print("\n⚡ Testing concurrent actions...")
    
    def make_action(session_name, token):
        """Make a draw_tile action and return the result."""
        headers = {"Authorization": f"Bearer {token}"}
        action_data = {"action_type": "draw_tile"}
        try:
            response = requests.post(
                f"{BASE_URL}/game/{game_id}/action",
                json=action_data,
                headers=headers
            )
            return session_name, response.status_code, response.json()
        except Exception as e:
            return session_name, 0, {"error": str(e)}
    
    # Only test concurrent actions if it's Player1's turn
    if game_state1['can_play']:
        print("Testing concurrent actions from both Player1 sessions...")
        
        # Use ThreadPoolExecutor to make truly concurrent requests
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(make_action, "Session1", token1_session1),
                executor.submit(make_action, "Session2", token1_session2)
            ]
            
            results = [future.result() for future in futures]
        
        success_count = 0
        for session_name, status_code, result in results:
            print(f"{session_name}: Status {status_code}")
            if status_code == 200:
                success_count += 1
                print(f"  ✅ {result['message']}")
            else:
                print(f"  ❌ {result.get('detail', result)}")
        
        if success_count == 1:
            print("✅ Exactly one action succeeded - concurrent action handling works!")
        elif success_count == 0:
            print("⚠️ No actions succeeded - check if it was Player1's turn")
        else:
            print(f"❌ {success_count} actions succeeded - race condition not handled properly")
    else:
        print("⚠️ Not Player1's turn, skipping concurrent action test")
    
    print("\n🎉 Multi-screen access tests completed!")


if __name__ == "__main__":
    try:
        test_multiscreen_access()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running on localhost:8090")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()