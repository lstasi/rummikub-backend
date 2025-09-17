#!/usr/bin/env python3
"""
Quick integration test - runs a single game for fast validation.
"""

import sys
import os

# Add the main integration test
sys.path.insert(0, os.path.dirname(__file__))

from test_integration import GameIntegrationTest

def main():
    """Run a quick single-game integration test."""
    print("🚀 Quick Rummikub Integration Test")
    print("Running single game for fast validation...\n")
    
    test_runner = GameIntegrationTest()
    result = test_runner.run_complete_game(2)  # Always use 2 players for speed
    
    print("\n" + "="*50)
    print("QUICK TEST SUMMARY")
    print("="*50)
    print(f"Game completed in {result['turns']} turns")
    print(f"Tiles placed: {result['tiles_placed']}")
    print(f"Board combinations: {result['board_combinations']}")
    print(f"Final status: {result['final_status']}")
    
    if 'winner' in result:
        print(f"🏆 Winner: {result['winner']}")
        return True
    else:
        print("⚡ Game completed without winner")
        return result['tiles_placed'] > 40  # Success if significant tiles were placed

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Quick integration test PASSED!")
    else:
        print("\n❌ Quick integration test had issues")
    sys.exit(0 if success else 1)