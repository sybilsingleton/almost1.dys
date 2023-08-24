Almost 1: Blockchain-Based Game on Dyson Protocol
=================================================

Overview
--------

Almost 1 is a game on the Dyson Protocol where players aim to get as close to 1 as possible without going over. Each "hit" gives a player a random float between 0 and 1, and the game operates in rounds with specific durations.

Constants
---------

-   `BASE_HIT_FEE`: Initial fee for hitting in a new game (default: free).
-   `BASE_PRIZE`: Initial prize amount for winners.
-   `ROUND_DURATION`: Duration of each game round (default: 120 seconds).

Functions
---------

### Main Functions

#### `hit(hand_id: str = None)`

Handles a hit action by a player. It verifies the fee, generates a random float, updates the hand data, and checks for the new highest, best, or smallest hand value. It also handles the extension of the round time if needed.

-   Input: `hand_id` (optional) - ID of the hand to hit.
-   Output: Tuple containing `round_id`, `hand_id`, and the updated value of the hand.

#### `claim_prize(round_id: str)`

Allows a player to claim their prize for a specific round after it has ended.

-   Input: `round_id` - ID of the round.
-   Output: Dictionary containing the claimed categories and their respective prizes.

### Query Functions

#### `get_highest_value(hand_id: str)`

#### `get_best_value(hand_id: str)`

#### `get_lowest_value(hand_id: str)`

Retrieve the highest, best, or lowest hand value for a specific round.

-   Input: `hand_id` - ID of the hand.
-   Output: List containing the queried value.

### Helper Functions

#### `get(index: str)`

#### `get_list(prefix: str, **kwargs: dict[str, str])`

Retrieve data from storage.

#### `_set(index: str, data)`

#### `_del(index: str)`

Update or delete data in storage.

#### `_get_next_id(key: str)`

#### `get_current_id(key: str)`

Retrieve the next available ID or the current ID for the given key.

#### `divvy(value: int)`

Divides the given value into predefined percentage splits (50%, 30%, 20%).

#### `get_or_create_current_round()`

Retrieves or creates the current round data.

-   Output: Tuple containing `round_id` and `round_data`.

Usage
-----

Players can join rounds and perform hits, aiming to get as close to 1 as possible. They can claim prizes for the closest to 1, the highest, and the lowest values. The game operates in rounds, allowing for continuous play.
