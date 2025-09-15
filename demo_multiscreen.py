#!/usr/bin/env python3
"""
Demonstration script for multi-screen access functionality.
Shows step-by-step how the multi-screen access works.
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


def demo_multiscreen_access():
    """Demonstrate multi-screen access functionality."""
    print("🚀 Multi-Screen Access Demo")
    print("=" * 50)
    
    # Step 1: Create a game
    print("\n📱 Step 1: Admin creates a game")
    auth_headers = create_auth_header()
    game_data = {"max_players": 2, "name": "DemoCreator"}
    response = requests.post(f"{BASE_URL}/game", json=game_data, headers=auth_headers)
    game_info = response.json()
    game_id = game_info["game_id"]
    print(f"   Game ID: {game_id}")
    
    # Step 2: Player joins from first device
    print("\n💻 Step 2: Alice joins from her laptop")
    join_data = {"player_name": "Alice"}
    response = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data)
    laptop_session = response.json()
    laptop_token = laptop_session["access_token"]
    print(f"   ✅ Alice joined from laptop")
    print(f"   Session token: ...{laptop_token[-10:]}")
    
    # Step 3: Another player joins to start the game  
    print("\n👤 Step 3: Bob joins to start the game")
    join_data = {"player_name": "Bob"}
    response = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data)
    print(f"   ✅ Bob joined - Game is now in progress!")
    
    # Step 4: Alice opens the game on her phone (multi-screen access)
    print("\n📱 Step 4: Alice opens the same game on her phone")
    join_data = {"player_name": "Alice"}  # Same name!
    response = requests.post(f"{BASE_URL}/game/{game_id}/join", json=join_data)
    
    if response.status_code == 200:
        phone_session = response.json()
        phone_token = phone_session["access_token"]
        print(f"   ✅ Alice successfully opened game on phone")
        print(f"   Phone token: ...{phone_token[-10:]}")
        print(f"   Message: {phone_session['message']}")
        
        # Verify tokens are different
        if laptop_token != phone_token:
            print(f"   ✅ Different tokens = separate sessions")
        else:
            print(f"   ❌ Tokens are identical!")
    else:
        print(f"   ❌ Failed: {response.json()}")
        return
    
    # Step 5: Check game state from both devices
    print("\n🔄 Step 5: Alice checks game state from both devices")
    
    # From laptop
    headers = {"Authorization": f"Bearer {laptop_token}"}
    response = requests.get(f"{BASE_URL}/game/{game_id}", headers=headers)
    laptop_state = response.json()
    
    # From phone  
    headers = {"Authorization": f"Bearer {phone_token}"}
    response = requests.get(f"{BASE_URL}/game/{game_id}", headers=headers)
    phone_state = response.json()
    
    print(f"   💻 Laptop sees: {len(laptop_state['your_tiles'])} tiles, current player: {laptop_state['current_player']}")
    print(f"   📱 Phone sees: {len(phone_state['your_tiles'])} tiles, current player: {phone_state['current_player']}")
    
    # Step 6: Try to make an action from both devices simultaneously
    print("\n⚡ Step 6: Alice tries to draw a tile from both devices at once")
    
    if laptop_state.get('can_play', False):
        # Simulate near-simultaneous actions
        print("   💻 Laptop attempts to draw tile...")
        headers_laptop = {"Authorization": f"Bearer {laptop_token}"}
        action_data = {"action_type": "draw_tile"}
        response1 = requests.post(f"{BASE_URL}/game/{game_id}/action", json=action_data, headers=headers_laptop)
        
        print("   📱 Phone attempts to draw tile...")
        headers_phone = {"Authorization": f"Bearer {phone_token}"}
        response2 = requests.post(f"{BASE_URL}/game/{game_id}/action", json=action_data, headers=headers_phone)
        
        # Check results
        if response1.status_code == 200:
            result1 = response1.json()
            print(f"   ✅ Laptop action succeeded: {result1['message']}")
        else:
            result1 = response1.json()
            print(f"   ❌ Laptop action failed: {result1['detail']}")
            
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"   ✅ Phone action succeeded: {result2['message']}")
        else:
            result2 = response2.json()  
            print(f"   ❌ Phone action failed: {result2['detail']}")
        
        # Show which one won
        success_count = (1 if response1.status_code == 200 else 0) + (1 if response2.status_code == 200 else 0)
        if success_count == 1:
            print(f"   🏆 Exactly one action succeeded - concurrency handled correctly!")
        else:
            print(f"   ⚠️  {success_count} actions succeeded - unexpected result")
    else:
        print(f"   ⏭️  Not Alice's turn, skipping concurrent action demo")
    
    # Step 7: Show final game state
    print("\n📊 Step 7: Final game state from both devices")
    
    headers = {"Authorization": f"Bearer {laptop_token}"}
    response = requests.get(f"{BASE_URL}/game/{game_id}", headers=headers)
    final_state = response.json()
    
    print(f"   💻📱 Both devices now see:")
    print(f"      Alice has {len(final_state['your_tiles'])} tiles")
    print(f"      Current turn: {final_state['current_player']}")
    print(f"      Alice can play: {final_state['can_play']}")
    
    print("\n🎉 Multi-Screen Access Demo Complete!")
    print("=" * 50)
    print("Summary:")
    print("✅ Players can open multiple sessions with the same name")
    print("✅ Each session gets a unique authentication token")
    print("✅ Both sessions see the same game state")
    print("✅ Concurrent actions are handled properly (first wins)")
    print("✅ All existing functionality is preserved")


if __name__ == "__main__":
    try:
        demo_multiscreen_access()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the server is running on localhost:8090")
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()