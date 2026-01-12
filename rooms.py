rooms={}
START_MONEY=1000

def create_room(room_id,host_id,pw,name):
    rooms[room_id]={
        "host":host_id,
        "password":pw,
        "players":{host_id:{"name":name,"money":START_MONEY,"bets":{}}},
        "clients":{}
    }

def join_room(room_id,uid,pw,name):
    if room_id not in rooms or rooms[room_id]["password"]!=pw:
        return False
    rooms[room_id]["players"].setdefault(uid,{
        "name":name,"money":START_MONEY,"bets":{}
    })
    return True

def remove_player(room_id,uid):
    r=rooms.get(room_id)
    if not r: return None
    r["players"].pop(uid,None)
    r["clients"].pop(uid,None)
    if uid==r["host"] and r["players"]:
        r["host"]=next(iter(r["players"]))
        return r["host"]
    if not r["players"]:
        rooms.pop(room_id,None)
    return None
