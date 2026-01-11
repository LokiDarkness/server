from fastapi import FastAPI, WebSocket, Query
import json, asyncio
from game import roll_dice, calc_reward, ICONS
from rooms import rooms, create_room, join_room, remove_player

app = FastAPI()
lobby_clients = []

# ===== LOBBY =====
@app.websocket("/lobby")
async def lobby(ws: WebSocket):
    await ws.accept()
    lobby_clients.append(ws)
    try:
        while True:
            data = json.loads(await ws.receive_text())
            if data["type"] == "CHAT":
                for c in lobby_clients:
                    await c.send_json(data)
    except:
        lobby_clients.remove(ws)

async def broadcast_rooms():
    data = [{"id": r, "host": rooms[r]["host"]} for r in rooms]
    for c in lobby_clients:
        await c.send_json({"type": "ROOM_LIST", "rooms": data})

# ===== GAME =====
@app.websocket("/ws/{room_id}/{uid}")
async def game(ws: WebSocket, room_id: str, uid: str, pw: str = Query(""), name: str = Query("")):
    await ws.accept()

    if room_id not in rooms:
        create_room(room_id, uid, pw, name)
        await broadcast_rooms()
    else:
        ok, msg = join_room(room_id, uid, pw, name)
        if not ok:
            await ws.send_json({"type": "ERROR", "msg": msg})
            await ws.close()
            return

    room = rooms[room_id]
    room["clients"][uid] = ws

    await ws.send_json({
        "type": "PLAYER_UPDATE",
        "players": room["players"],
        "host": room["host"]
    })

    try:
        while True:
            data = json.loads(await ws.receive_text())

            if data["type"] == "PLACE_BET":
                icon = data["icon"]
                amt = data["amount"]
                p = room["players"][uid]

                if icon in ICONS and p["money"] >= amt:
                    p["money"] -= amt
                    p["bets"][icon] = p["bets"].get(icon, 0) + amt

            if data["type"] == "HOST_ROLL" and uid == room["host"]:
                dice = roll_dice()

                for c in room["clients"].values():
                    await c.send_json({"type": "ROLL_START"})

                await asyncio.sleep(2)

                for p in room["players"].values():
                    p["money"] += calc_reward(p["bets"], dice)
                    p["bets"] = {}

                for c in room["clients"].values():
                    await c.send_json({
                        "type": "ROLL_RESULT",
                        "dice": dice,
                        "players": room["players"],
                        "host": room["host"]
                    })
    except:
        remove_player(room_id, uid)
        await broadcast_rooms()
