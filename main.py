from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory= "templates")




class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def emit_message(self, message: str, websocket: WebSocket):
        for connection in self.active_connections:
            if connection !=  websocket:
                await connection.send_text(message)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

def sent_message(message: str, username):
    return f"""
            <div id="message"  hx-swap-oob="beforeend">
                <div class="message user">
                <span>~{username}</span>
                    {message}
                </div>
            </div>"""

def received_message(message, username):
    return f"""
            <div id="message"  hx-swap-oob="beforeend">
                <div class="message other">
                    <span>{username}</span>
                    {message}
                </div>
            </div>"""

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    try: 
        return templates.TemplateResponse("index.html", {"request": request})
    except: 
        return """
            <html> 
                <body>
                    <p>Error occured</p>
                </body>
            <html>
        """
@app.get("/chat", response_class=HTMLResponse)
async def chat(request:Request, username: str, chatroom: str): 
    return templates.TemplateResponse("chat.html", {"request": request, "chatroom": chatroom, "username": username}) 
        


@app.websocket("/chatroom")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get('message-text')
            await manager.send_personal_message(sent_message(message, username), websocket)
            await manager.emit_message(received_message(message, username), websocket) 
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"#{username} left the chat")
