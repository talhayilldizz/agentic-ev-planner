from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from tools.db_tool import search_vehicle, search_charging_stations
from tools.calc_tool import calculate_energy_consumption
import os
from dotenv import load_dotenv
from tools.web_tool import web_search
from tools.calc_tool import calculate_energy_consumption
from tools.route_tool import plan_smart_ev_route
from tools.price_tool import calculate_price


load_dotenv()

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


SYSTEM_PROMPT = """
Sen, elektrikli araçlar ve şarj istasyonları konusunda uzman, premium bir yapay zeka asistanısın. 
Kullanıcılara, elektrikli araçların özelliklerini (batarya, menzil, hızlı şarj), şarj istasyonlarını ve tüketim/menzil hesaplamalarını yapma konusunda yardımcı oluyorsun.
Kurallar:
1. Her zaman kibar, profesyonel ve enerjik bir dil kullan.
2. Bir araç veya istasyon sorulduğunda ÖNCE veritabanı araçlarını (search_vehicle veya search_charging_stations) kullan.
3. Bulduğun sonuçları kullanıcıya çok temiz, okunabilir ve Markdown formatında sun.
4. Kullanıcı güncel bir haber veya fiyat sorarsa doğrudan web_search aracını kullan.
5. Eğer toollarda arama yapıp bir sonuç bulamazsan hemen ardından web search yap ve uygun cevabı bul.
6. Kullanıcı selam verdiğinde sıcak bir karşılama yap ve ne yapabildiğini kısaca söyle.
7. Sorulan soru Arabalar, elektrikli arabalar veya şarj istasyonları hakkında değilse bilgin olmadığını belirt.
8. Kullanıcı bir rota veya yolculuk (başlangıç ve bitiş) verip yol planlaması isterse KESİNLİKLE 'plan_smart_ev_route' aracını kullan! (Örn: İstanbul'dan Antalya'ya gidiyorum...). Bu araç tüm molaları otomatik hesaplar.
9. Eğer aracın batarya kapasitesini bilmiyorsan, rotayı hesaplamadan ÖNCE search_vehicle veya web_search ile kapasiteyi bul, sonra plan_smart_ev_route aracını çalıştır. Başka hesaplama aracı kullanma.
10. ÇOK ÖNEMLİ: Eğer araçlar (özellikle plan_smart_ev_route) sana en sonda bir ```json kod bloğu döndürürse, bu bloğu KESİNLİKLE SİLME ve değiştirmeden kendi nihai yanıtının en sonuna birebir kopyala. Bu, uygulamanın harita çizebilmesi için hayati önem taşır!
11. Kullanıcı belirli bir şarj firmasının (operatörün) şarj tarifesini/fiyatını sorarsa (örn: ZES fiyatı, Trugo DC şarj ücreti nedir?), KESİNLİKLE 'calculate_price' aracını kullan ve çıkan fiyatı söyle!
"""

llm = ChatOpenAI(
    model = "gpt-4o-mini",
    temperature = 0.2
)

tools = [
    search_charging_stations,
    search_vehicle,
    web_search,
    calculate_energy_consumption,
    plan_smart_ev_route,
    calculate_price
]

llm_with_tools = llm.bind_tools(tools)
def call_model(
    state: State
):
    messages=state["messages"]
    if len(messages) == 1 and isinstance(messages[0], HumanMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    response = llm_with_tools.invoke(messages)
    return {
        "messages": [response]
    }

workflow = StateGraph(State)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)