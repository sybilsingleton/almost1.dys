from dys import _chain, SCRIPT_ADDRESS, CALLER, get_coins_sent

import random
from decimal import Decimal
from datetime import datetime, timedelta
import json


BASE_HIT_FEE = {"denom": "almost1.dys", "amount": 0}  # new game is always free
BASE_PRIZE = {"denom": "almost1.dys", "amount": 100}
ROUND_DURATION = {"seconds": 120}
FEE_SENT = int(
    {c["denom"]: Decimal(c["amount"]) for c in get_coins_sent()}.get(
        BASE_HIT_FEE["denom"], 0
    )
)


NOW = datetime.now()


def hit(hand_id: str = None):
    round_id, round_data = get_or_create_current_round()
    assert (
        FEE_SENT >= round_data["hit_fee"]["amount"]
    ), f"Incorrect coins for hitting: got {FEE_SENT} needed {round_data['hit_fee']}"

    # Burn the hit fee
    if FEE_SENT > 0:
        burn = FEE_SENT // 2
        additional_prize = FEE_SENT - burn
        _chain(
            "names/sendMsgBurnCoins",
            owner=SCRIPT_ADDRESS,
            amount=str(burn) + BASE_HIT_FEE["denom"],
        )
        best_prize, highest_prize, lowest_prize = divvy(additional_prize)

        round_data["best"]["prize"] += best_prize
        round_data["highest"]["prize"] += highest_prize
        round_data["lowest"]["prize"] += lowest_prize

    # increase hit fee 1 every time
    round_data["hit_fee"]["amount"] += 1
    round_data["hits"] += 1

    if hand_id is None:
        # Get the next available hand_id
        hand_id = _get_next_id(f"rounds/{round_id}/next_hand_id")

        hand_data = {
            "address": CALLER,
            "hits": [],
            "value": 0,
            "hand_id": hand_id,
            "round_id": round_id,
        }
        _set(f"hand/{round_id}/{hand_id}", hand_data)
        round_data["hands"] += 1
    else:
        hand_data = get(f"hand/{round_id}/{hand_id}")
        assert hand_data, f"This round_id [{round_id}] does have this hand[{hand_id}]"
        assert CALLER == hand_data["address"], "Caller does not match hand address"

    assert hand_data["value"] < 1, f"Already bust: {hand_data['value']}"

    # remove lookup based on original value
    _del(f"value/{round_id}/{hand_data['value']}")

    # Generate a random float and update the player's hits
    random_float = random.uniform(0, 1)
    hand_data["value"] += random_float
    hand_data["hits"].append(random_float)

    _set(
        f"value/{round_id}/{hand_data['value']}",
        {"hand_id": hand_id, "value": hand_data["value"]},
    )

    # Check for new largest, best, or smallest hand value and extend the round if needed
    highest = (
        get_list("value/" + round_id, pagination={"reverse": True, "limit": 1})
        or [None]
    )[0]
    best = (
        get_list("value/" + round_id + "/0.", pagination={"reverse": True, "limit": 1})
        or [None]
    )[0]
    lowest = (
        get_list("value/" + round_id, pagination={"reverse": False, "limit": 1})
        or [None]
    )[0]
    round_data["highest"] |= highest
    round_data["best"] |= best
    round_data["lowest"] |= lowest

    if hand_id in [highest, best, lowest]:
        # Extend end_time from the current timestamp
        end_time = NOW + timedelta(**ROUND_DURATION)
        round_data["end_time"] = str(end_time)

    # remove lookup based on original value
    _set(f"hand/{round_id}/{hand_id}", hand_data)
    _set(f"rounds/{round_id}", round_data)

    # Return the round_id, hand_id, and random float
    return round_id, hand_id, hand_data["value"]


def claim_prize(round_id: str):
    # Retrieve round data
    round_data = get(f"rounds/{round_id}")
    assert round_data, f"Round with id {round_id} does not exist"

    # Check if the round has ended
    assert str(NOW) > round_data["end_time"], "Round has not ended yet"

    claimed_categories = {}

    # Loop over the highest, best, and lowest hands
    for category in ["highest", "best", "lowest"]:
        hand_id = round_data[category]["hand_id"]
        assert hand_id is not None, f"No hand for {category} category"

        # Retrieve hand data
        hand_data = get(f"hand/{round_id}/{hand_id}")
        assert hand_data, f"Hand with id {hand_id} does not exist"

        # Assert that the caller is the player
        assert CALLER == hand_data["address"], "Caller does not match hand address"

        # Check if the prize has already been claimed
        assert not round_data[category][
            "claimed"
        ], f"{category.capitalize()} prize already claimed"

        # Send the prize to the caller
        coins = [
            {"amount": round_data[category]["prize"], "denom": BASE_PRIZE["denom"]}
        ]
        _chain(
            "cosmos.bank.v1beta1/sendMsgSend",
            from_address=SCRIPT_ADDRESS,
            to_address=CALLER,
            amount=coins,
        )

        # Mark the prize as claimed
        round_data[category]["claimed"] = True
        claimed_categories[category] = coins[0]
        # Update round data
        _set(f"rounds/{round_id}", round_data)

    return claimed_categories


def get_highest_value(hand_id: str):
    return get_list(
        "value/" + round_id,
        pagination={"reverse": True, "limit": 1},
    )


def get_best_value(hand_id: str):
    return get_list(
        "value/" + round_id + "/0.",
        pagination={"reverse": True, "limit": 1},
    )


def get_lowest_value(hand_id: str):
    return get_list(
        "value/" + round_id,
        pagination={"reverse": False, "limit": 1},
    )


# Helper Function to Retrieve Data
def get(index: str):
    result = _chain("dyson/QueryStorage", index=SCRIPT_ADDRESS + "/" + index)["result"]
    if not result:
        return None
    return json.loads(result.get("storage", {}).get("data"))


# Helper Function to Retrieve Data
def get_list(prefix: str, **kwargs: dict[str, str]):  # kwargs for pagination
    result = _chain(
        "dyson/QueryPrefixStorage", prefix=SCRIPT_ADDRESS + "/" + prefix, **kwargs
    )["result"]["storage"]
    return [json.loads(r["data"]) for r in result]


# Helper Function to Update Data
def _set(index: str, data):
    _chain(
        "dyson/sendMsgUpdateStorage",
        creator=SCRIPT_ADDRESS,
        index=SCRIPT_ADDRESS + "/" + index,
        data=json.dumps(data),
        force=True,
    )


# Helper Function to delete Data
def _del(index: str):
    _chain(
        "dyson/sendMsgDeleteStorage",
        creator=SCRIPT_ADDRESS,
        index=SCRIPT_ADDRESS + "/" + index,
    )


def _get_next_id(key: str):
    # Get the next available ID for the given key
    next_id = (get(key) or 0) + 1

    # Increment and store the next ID for future use
    _set(key, next_id)

    # Convert to a left-padded hex number
    return f"{next_id:04}"


def get_current_id(key: str):
    # Get the next available ID for the given key
    current_id = get(key) or 1

    # Convert to a left-padded hex number
    return f"{current_id:04}"


def divvy(value: int):
    fifty_percent = value * 50 // 100
    thirty_percent = value * 30 // 100
    twenty_percent = value * 20 // 100

    # Calculate the remainder if there's any
    remainder = value - fifty_percent - thirty_percent - twenty_percent

    return fifty_percent, thirty_percent, twenty_percent + remainder


def get_or_create_current_round():
    round_id = get_current_id("round_id")
    round_data = get(f"rounds/{round_id}")

    if round_data:
        if str(NOW) < round_data["end_time"]:
            return round_id, round_data
        round_id = _get_next_id("round_id")

    # Create a new round if none exists or the current round is over
    end_time = str(NOW + timedelta(**ROUND_DURATION))

    best_prize, highest_prize, lowest_prize = divvy(BASE_PRIZE["amount"])
    round_data = {
        "round_id": round_id,
        "end_time": end_time,
        "highest": {
            "prize": highest_prize,
            "claimed": False,
            "hand_id": None,
            "value": None,
        },
        "best": {"prize": best_prize, "claimed": False, "hand_id": None, "value": None},
        "lowest": {
            "prize": lowest_prize,
            "claimed": False,
            "hand_id": None,
            "value": None,
        },
        "hit_fee": BASE_HIT_FEE,
        "hands": 0,
        "hits": 0,
    }
    _set(f"rounds/{round_id}", round_data)

    return round_id, round_data
