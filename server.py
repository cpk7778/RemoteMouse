"""iPhone -> Windows PC 마우스 컨트롤러
실행: python server.py   (pip install aiohttp pyautogui)
아이폰 Safari에서 출력된 주소로 접속 후 PIN 입력.
"""
import asyncio, json, random, socket
from aiohttp import web, WSMsgType
import pyautogui

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

PORT = 8000
PIN = f"{random.randint(0, 9999):04d}"

HTML = r"""<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>마우스</title>
<style>
*{box-sizing:border-box;-webkit-user-select:none;user-select:none;-webkit-touch-callout:none;-webkit-tap-highlight-color:transparent}
html,body{margin:0;height:100%;background:#111;color:#eee;font-family:-apple-system,sans-serif;overflow:hidden;overscroll-behavior:none}
#login{display:flex;flex-direction:column;gap:16px;align-items:center;justify-content:center;height:100%}
#login input{font-size:32px;width:160px;text-align:center;padding:10px;border-radius:12px;border:0;background:#222;color:#fff;letter-spacing:8px;-webkit-user-select:text;user-select:text}
button{font-size:18px;border:0;border-radius:14px;background:#2a6cf0;color:#fff;padding:14px 24px}
#app{display:none;flex-direction:column;height:100%;padding:env(safe-area-inset-top) 10px env(safe-area-inset-bottom)}
#pad{flex:1;margin:10px 0;border-radius:20px;background:#1e1e1e;border:2px solid #333;display:flex;align-items:center;justify-content:center;color:#555;touch-action:none}
#bar{display:flex;gap:10px;margin-bottom:10px}
#bar button{flex:1;padding:22px 0;background:#333}
#st{text-align:center;font-size:13px;color:#888;padding-bottom:6px}
</style></head><body>
<div id="login">
  <div>PC에 표시된 PIN 입력</div>
  <input id="pin" inputmode="numeric" maxlength="4" autocomplete="off">
  <button id="go">연결</button>
  <div id="err" style="color:#f66"></div>
</div>
<div id="app">
  <div id="pad">터치패드<br>1손가락: 이동 · 탭: 클릭<br>2손가락: 스크롤 · 2손가락 탭: 우클릭</div>
  <div id="bar"><button id="l">좌클릭</button><button id="r">우클릭</button></div>
  <div id="st">연결됨</div>
</div>
<script>
let ws;
const $=id=>document.getElementById(id);
const send=o=>{ if(ws&&ws.readyState===1) ws.send(JSON.stringify(o)); };
function connect(){
  ws=new WebSocket(`ws://${location.host}/ws?pin=${$('pin').value}`);
  ws.onopen=()=>{$('login').style.display='none';$('app').style.display='flex';$('st').textContent='연결됨';};
  ws.onclose=e=>{ if($('app').style.display==='flex'){$('st').textContent='연결 끊김 - 새로고침';}
                  else {$('err').textContent='PIN이 틀렸거나 연결 실패';} };
}
$('go').onclick=connect;
$('pin').addEventListener('keydown',e=>{if(e.key==='Enter')connect();});

const pad=$('pad'), SENS=2.2;
let lx=0,ly=0,moved=0,t0=0,maxTouches=0;
pad.addEventListener('touchstart',e=>{
  e.preventDefault();
  if(e.touches.length===1){moved=0;t0=Date.now();maxTouches=1;}
  maxTouches=Math.max(maxTouches,e.touches.length);
  const c=center(e.touches); lx=c.x; ly=c.y;
},{passive:false});
pad.addEventListener('touchmove',e=>{
  e.preventDefault();
  const c=center(e.touches), dx=c.x-lx, dy=c.y-ly;
  lx=c.x; ly=c.y; moved+=Math.abs(dx)+Math.abs(dy);
  if(e.touches.length>=2) send({t:'scroll',dy:Math.round(-dy*0.5)});
  else send({t:'move',dx:Math.round(dx*SENS),dy:Math.round(dy*SENS)});
},{passive:false});
pad.addEventListener('touchend',e=>{
  e.preventDefault();
  if(e.touches.length===0 && moved<8 && Date.now()-t0<300){
    send({t: maxTouches>=2?'rclick':'click'});
  }
},{passive:false});
function center(ts){let x=0,y=0;for(const t of ts){x+=t.clientX;y+=t.clientY;}return{x:x/ts.length,y:y/ts.length};}
$('l').onclick=()=>send({t:'click'});
$('r').onclick=()=>send({t:'rclick'});
</script></body></html>
"""


async def index(request):
    return web.Response(text=HTML, content_type="text/html")


async def ws_handler(request):
    if request.query.get("pin") != PIN:
        return web.Response(status=403, text="bad pin")
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    async for msg in ws:
        if msg.type != WSMsgType.TEXT:
            continue
        try:
            m = json.loads(msg.data)
            t = m["t"]
            if t == "move":
                pyautogui.moveRel(int(m["dx"]), int(m["dy"]), _pause=False)
            elif t == "click":
                pyautogui.click()
            elif t == "rclick":
                pyautogui.rightClick()
            elif t == "scroll":
                pyautogui.scroll(int(m["dy"]) * 20)
        except Exception as e:
            print("error:", e)
    return ws


def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    app = web.Application()
    app.add_routes([web.get("/", index), web.get("/ws", ws_handler)])
    print(f"\n아이폰 Safari에서 접속: http://{local_ip()}:{PORT}")
    print(f"PIN: {PIN}\n(종료: Ctrl+C)\n")
    web.run_app(app, host="0.0.0.0", port=PORT, print=None)


if __name__ == "__main__":
    main()