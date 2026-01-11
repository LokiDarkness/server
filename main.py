from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
import asyncio
import json

from game import roll_dice, calc_reward, ICONS
from rooms import rooms, create_room, join_room, remove_player

app = FastAPI()

# ======================
# LOBBY
# ======================
lobby_clients = []

@app.websocket("/lobby")
async def lobby(ws: WebSocket):
    await ws.accept()
    lobby_clients.append(ws)

    try:
        while True:
            data = json.loads(await ws.receive_text())

            if data["type"] == "CHAT":
                for c in lobby_clients[:]:
                    try:
                        await c.send_json(data)
                    except:
                        lobby_clients.remove(c)

    except WebSocketDisconnect:
        if ws in lobby_clients:
            lobby_clients.remove(ws)


async def broadcast_rooms():
    data = [
        {
            "id": room_id,
            "host": rooms[room_id]["host"]
        }
        for room_id in rooms
    ]

    for c in lobby_clients[:]:
        try:
            await c.send_json({
                "type": "ROOM_LIST",
                "rooms": data
            })
        except:
            lobby_clients.remove(c)

# ======================
# GAME ROOM
# ======================
@app.websocket("/ws/{room_id}/{uid}")
async def game_ws(
    ws: WebSocket,
    room_id: str,
    uid: str,
    pw: str = Query(""),
    name: str = Query("")
):
    await ws.accept()

    # tạo hoặc join phòng
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

    # gửi trạng thái ban đầu
    await ws.send_json({
        "type": "PLAYER_UPDATE",
        "players": room["players"],
        "host": room["host"]
    })

    try:
        while True:
            data = json.loads(await ws.receive_text())

            # ======================
            # ĐẶT CƯỢC
            # ======================
            if data["type"] == "PLACE_BET":
                icon = data["icon"]
                amount = int(data["amount"])
                player = room["players"].get(uid)

                if (
                    icon in ICONS
                    and amount > 0
                    and player["money"] >= amount
                ):
                    player["money"] -= amount
                    player["bets"][icon] = (
                        player["bets"].get(icon, 0) + amount
                    )

            # ======================
            # HOST ROLL
            # ======================
            if data["type"] == "HOST_ROLL" and uid == room["host"]:
                dice = roll_dice()

                # báo bắt đầu lắc
                for c in room["clients"].values():
                    await c.send_json({"type": "ROLL_START"})

                await asyncio.sleep(2)

                # tính tiền
                for p in room["players"].values():
                    p["money"] += calc_reward(p["bets"], dice)
                    p["bets"] = {}

                # gửi kết quả
                for c in room["clients"].values():
                    await c.send_json({
                        "type": "ROLL_RESULT",
                        "dice": dice,
                        "players": room["players"],
                        "host": room["host"]
                    })

    except WebSocketDisconnect:
        remove_player(room_id, uid)
        await broadcast_rooms()
