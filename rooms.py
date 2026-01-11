rooms = {}
START_MONEY = 1000

def create_room(room_id, host_id, password, name):
    rooms[room_id] = {
        "host": host_id,
        "password": password,
        "players": {
            host_id: {
                "name": name,
                "money": START_MONEY,
                "bets": {}
            }
        },
        "clients": {}
    }

def join_room(room_id, uid, password, name):
    if room_id not in rooms:
        return False, "Room not found"

    room = rooms[room_id]

    if room["password"] != password:
        return False, "Wrong password"

    if uid not in room["players"]:
        room["players"][uid] = {
            "name": name,
            "money": START_MONEY,
            "bets": {}
        }

    return True, "OK"

def remove_player(room_id, uid):
    room = rooms.get(room_id)
    if not room:
        return

    room["players"].pop(uid, None)
    room["clients"].pop(uid, None)

    # chuyển host nếu host thoát
    if uid == room["host"]:
        if room["players"]:
            room["host"] = next(iter(room["players"]))
        else:
            rooms.pop(room_id, None)
