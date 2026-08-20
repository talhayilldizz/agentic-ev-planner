# Dosya: backend/main.py
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from agent.graph import graph
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="EV AI Assistant API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"

@app.post("/chat")
@limiter.limit("10/minute")
def chat_endpoint(req: ChatRequest, request: Request):
    user_msg = HumanMessage(content=req.message)
    
    config = {"configurable": {"thread_id": req.session_id}}
    
    print(f"\n\n=======================================================", flush=True)
    print(f"KULLANICI [{req.session_id}]: {req.message}", flush=True)
    
    final_response = ""
    map_json_payload = ""
    # graph.invoke yerine graph.stream kullanıp aradaki adımları ekrana (terminale) basıyoruz
    for event in graph.stream({"messages": [user_msg]}, config=config):
        for node, state in event.items():
            print(f"--> 🔄 [LANGGRAPH] Düğüm (Node) çalıştı: {node.upper()}", flush=True)
            last_msg = state["messages"][-1]
            
            if node == "agent":
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    for tc in last_msg.tool_calls:
                        print(f"    🛠️  YAPAY ZEKA KARARI: '{tc['name']}' aracı çağrılıyor!", flush=True)
                        print(f"    Parametreler: {tc['args']}", flush=True)
                else:
                    print("     YAPAY ZEKA KARARI: Araç kullanmaya gerek yok, doğrudan yanıt veriliyor.", flush=True)
                    
            elif node == "tools":
                print(f"    ARAÇ YANITI DÖNDÜ! (Çıktı boyutu: {len(str(last_msg.content))} karakter)", flush=True)
                print(f"    İlk 100 Karakter: {str(last_msg.content)[:100]}...", flush=True)

                if "```json" in last_msg.content:
                    parts = last_msg.content.split("```json")
                    if len(parts) > 1:
                        json_str = parts[1].split("```")[0]
                        map_json_payload = f"\n\n```json{json_str}```"



            # Her adımda en son mesajı güncel tutuyoruz ki en son kullanıcıya bunu dönelim
            final_response = last_msg.content

    print(f"YAPAY ZEKA YANITI: {final_response[:100]}...", flush=True)
    print(f"=======================================================\n", flush=True)
    
    if map_json_payload:
        final_response += map_json_payload


    return {"response": final_response}

@app.get("/")
def read_root():
    return {"status": "Backend is running and Graph is ready!"}
