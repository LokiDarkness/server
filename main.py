from fastapi import FastAPI,WebSocket,WebSocketDisconnect,Query
import asyncio,json
from collections import Counter
from game import roll_dice,calc_reward
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
            for c in lobby_clients:
                await c.send_json(d)
    except:
        lobby_clients.remove(ws)

@app.websocket("/ws/{room}/{uid}")
async def game_ws(ws:WebSocket,room:str,uid:str,pw:str=Query(""),name:str=Query("")):
    await ws.accept()
    if room not in rooms:
        create_room(room,uid,pw,name)
    elif not join_room(room,uid,pw,name):
        await ws.close();return

    r=rooms[room]
    r["clients"][uid]=ws

    try:
        while True:
            d=json.loads(await ws.receive_text())
            if d["type"]=="HOST_ROLL" and uid==r["host"]:
                for c in r["clients"].values():
                    await c.send_json({"type":"ROLL_COUNTDOWN","from":3})
                await asyncio.sleep(3)

                dice=roll_dice()
                wins=dict(Counter(dice))

                for p in r["players"].values():
                    p["money"]+=calc_reward(p["bets"],dice)
                    p["bets"]={}

                for c in r["clients"].values():
                    await c.send_json({
                        "type":"ROLL_RESULT",
                        "dice":dice,
                        "wins":wins,
                        "players":r["players"],
                        "host":r["host"]
                    })
    except WebSocketDisconnect:
        remove_player(room,uid)
