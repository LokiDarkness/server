rooms = {}
START_MONEY = 1000

def create_room(room_id, host_id, password, name):
    rooms[room_id] = {
        "host": host_id,
        "password": password,
        "players": {
            host_id: {"name": name, "money": START_MONEY, "bets": {}}
        },
        "clients": {}
    }

def join_room(room_id, uid, password, name):
    if room_id not in rooms:
        return False, "No room"
    if rooms[room_id]["password"] != password:
        return False, "Wrong password"
    rooms[room_id]["players"].setdefault(uid, {
        "name": name, "money": START_MONEY, "bets": {}
    })
    return True, "OK"

def remove_player(room_id, uid):
    r = rooms.get(room_id)
    if not r: return
    r["players"].pop(uid, None)
    r["clients"].pop(uid, None)
    if uid == r["host"]:
        if r["players"]:
            r["host"] = next(iter(r["players"]))
        else:
            rooms.pop(room_id)
