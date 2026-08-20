from langchain_core.tools import tool
from ddgs import DDGS
@tool
def web_search(query: str) -> str:
    """Elektrikli araç fiyatları, güncel haberler veya internette genel bilgi aramak için kullan."""
    try:
        # İnternete bağlanıp en iyi 3 sonucu çekiyoruz
        results = DDGS().text(query, max_results=3)
        return str(results)
    except Exception as e:
        return f"Arama sırasında hata oluştu: {str(e)}"
