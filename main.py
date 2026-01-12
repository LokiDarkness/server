from fastapi import FastAPI,WebSocket,WebSocketDisconnect,Query
import asyncio,json
from game import roll_dice,calc_reward,ICONS
from rooms import rooms,create_room,join_room,remove_player

app=FastAPI()
lobby_clients=[]

@app.websocket("/lobby")
async def lobby(ws:WebSocket):
    await ws.accept()
    lobby_clients.append(ws)
    try:
        while True:
            d=json.loads(await ws.receive_text())
            if d["type"]=="CHAT":
                for c in lobby_clients[:]:
                    try: await c.send_json(d)
                    except: lobby_clients.remove(c)
    except WebSocketDisconnect:
        lobby_clients.remove(ws)

async def broadcast_rooms():
    for c in lobby_clients[:]:
        try:
            await c.send_json({
                "type":"ROOM_LIST",
                "rooms":[{"id":r,"host":rooms[r]["host"]} for r in rooms]
            })
        except: lobby_clients.remove(c)

@app.websocket("/ws/{room_id}/{uid}")
async def game_ws(ws:WebSocket,room_id:str,uid:str,pw:str=Query(""),name:str=Query("")):
    await ws.accept()
    if room_id not in rooms:
        create_room(room_id,uid,pw,name)
        await broadcast_rooms()
    elif not join_room(room_id,uid,pw,name):
        await ws.close(); return

    room=rooms[room_id]
    room["clients"][uid]=ws

    await ws.send_json({
        "type":"PLAYER_UPDATE",
        "players":room["players"],
        "host":room["host"]
    })

    try:
        while True:
            d=json.loads(await ws.receive_text())
            if d["type"]=="HOST_ROLL" and uid==room["host"]:
                dice=roll_dice()
                for c in room["clients"].values():
                    await c.send_json({"type":"ROLL_START"})
                await asyncio.sleep(2)
                for p in room["players"].values():
                    p["money"]+=calc_reward(p["bets"],dice)
                    p["bets"]={}
                for c in room["clients"].values():
                    await c.send_json({
                        "type":"ROLL_RESULT",
                        "dice":dice,
                        "players":room["players"],
                        "host":room["host"]
                    })
    except WebSocketDisconnect:
        new_host=remove_player(room_id,uid)
        if room_id in rooms and new_host:
            for c in rooms[room_id]["clients"].values():
                await c.send_json({
                    "type":"SYSTEM",
                    "msg":f"👑 {rooms[room_id]['players'][new_host]['name']} đã trở thành HOST"
                })
        await broadcast_rooms()
