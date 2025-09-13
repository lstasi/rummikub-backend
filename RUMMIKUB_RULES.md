# Rummikub Game Rules

## Overview
Rummikub is a tile-based game for 2-4 players, played with 104 number tiles and 2 joker tiles. The goal is to be the first player to play all tiles from your rack.

## Game Components
- **106 tiles total:**
  - 104 numbered tiles: Numbers 1-13 in four colors (black, red, blue, orange) - 2 sets of each
  - 2 joker tiles

## Initial Setup
1. Each player draws 14 tiles randomly from the pool
2. The remaining tiles form the "pool" for drawing
3. Players place their tiles on their rack (hidden from other players)

## Game Objective
Be the first player to play all tiles from your rack by placing them on the board in valid combinations.

## Valid Combinations

### Groups
- **Definition:** 3 or 4 tiles of the same number in different colors
- **Examples:**
  - {3♠, 3♥, 3♦} (3 in black, red, blue)
  - {7♠, 7♥, 7♦, 7♣} (7 in all four colors)

### Runs
- **Definition:** 3 or more consecutive numbers in the same color
- **Examples:**
  - {4♠, 5♠, 6♠} (consecutive black tiles)
  - {9♥, 10♥, 11♥, 12♥, 13♥} (consecutive red tiles)

## Initial Meld Requirement
- Before a player can place tiles on the board, they must make an "initial meld"
- The initial meld must have a total value of at least 30 points
- Tile values: Numbers 1-13 are worth their face value, jokers are worth the value of the tile they represent

## Gameplay

### Turn Structure
1. **Option 1: Play tiles** - Place valid combinations on the board
2. **Option 2: Draw a tile** - If unable to play, draw one tile from the pool

### Playing Tiles
- Players can add tiles to existing combinations on the board
- Players can rearrange existing combinations to create new valid ones
- All combinations on the board must remain valid after any changes
- If a player starts rearranging the board, they must complete all changes in their turn

### Joker Rules
- Jokers can substitute for any tile in a combination
- A joker's value is determined by its position in the combination
- Players can retrieve a joker from the board by replacing it with the actual tile and using the joker elsewhere in the same turn

## Winning
- The first player to play all tiles from their rack wins the round
- Game can be played for multiple rounds with scoring

## Scoring (Optional)
- Winner scores zero points
- Other players score penalty points equal to the sum of tiles remaining in their rack
- Play to a predetermined point limit (common: first to 500+ points loses)

## Special Rules for This Implementation
- No time limits on turns
- Players join games using invite codes
- Game state only shows each player's own tiles
- Actions available: placing tiles on board, rearranging board combinations
- Session-based gameplay after initial join