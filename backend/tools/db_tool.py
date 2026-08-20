import os
from sqlalchemy import create_engine, text
from langchain_core.tools import tool

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'ev_database.db')

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

def normalize_text(text: str) -> str:
    """Türkçe İ/ı karakter karmaşasını önlemek için standart İngilizce I'ya çevirir."""
    return text.upper().replace('İ', 'I').replace('ı', 'I')

def run_query(sql_query: str, params: dict = None):
    if params is None:
        params = {}
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query), params)
            rows = [dict(row._mapping) for row in result]
            return rows
    except Exception as e:
        return f"Veritabanı hatası: {str(e)}"

@tool
def search_vehicle(
    query: str
) -> str:
    """
    Kullanıcının marka, model veya marka + model sorgusuna göre
    elektrikli araç bilgilerini getirir.
    Örnek:
    'Tesla'
    'Model Y'
    'Tesla Model Y'
    """


    sql = """
    SELECT brand, model, battery_capacity_kwh, range_km, fast_charging_power_kw_dc 
    FROM vehicles 
    WHERE brand LIKE :search_term 
       OR model LIKE :search_term 
       OR (brand || ' ' || model) LIKE :search_term
    LIMIT 10
    """

    search_term = f"%{query}%"
    results = run_query(sql, 
    {
        "search_term": search_term
    }
    )
    
    if not isinstance(results, list) or not results:
        return f"'{query}' aramasına uygun araç bulunamadı."
    
    output = "Bulunan Araçlar:\n"
    for r in results:
        output += f"- {r['brand']} {r['model']}: {r['battery_capacity_kwh']} kWh batarya, {r['range_km']} km menzil, {r['fast_charging_power_kw_dc']} kW Hızlı Şarj.\n"
    return output

@tool
def search_charging_stations(location: str) -> str:
    """
    Belirli bir şehirdeki (province) veya ilçedeki (district) şarj istasyonlarını getirir.
    Örnek: 'Rize', 'Trabzon', 'İstanbul', 'İstanbul Pendik', 'Kadıköy'
    """
    words = normalize_text(location).split()
    
    if not words:
        return "Lütfen geçerli bir konum girin."
    conditions = []
    params = {}
    
    for i, word in enumerate(words):
        param_name = f"word_{i}"
        conditions.append(
            f"(REPLACE(UPPER(province), 'İ', 'I') LIKE :{param_name} OR "
            f"REPLACE(UPPER(district), 'İ', 'I') LIKE :{param_name})"
        )
        params[param_name] = f"{word}%"
        
    where_clause = " AND ".join(conditions)
    
    sql = f"""
    SELECT brand, province, district, socket_count, max_power_kw, connector_type, latitude, longitude 
    FROM charging_stations 
    WHERE {where_clause}
    LIMIT 10
    """
    
    results = run_query(sql, params)
    
    if not isinstance(results, list) or not results:
        return f"'{location}' aramasına uygun şarj istasyonu bulunamadı."
    
    output = f"{location.title()} Bölgesi Şarj İstasyonları:\n"
    for r in results:
        maps_link = f"https://www.google.com/maps/search/?api=1&query={r['latitude']},{r['longitude']}"
        
        output += f"- {r['brand']} ({r['province']} - {r['district']}): {r['socket_count']} soket, {r['max_power_kw']} kW Max (Tip: {r['connector_type']}) - [📍 Haritada Gör]({maps_link})\n"
        
    return output


if __name__ == "__main__":
    print("--- Araç Arama Testi ---")
    print(search_vehicle.invoke({"query": "Peugeot"}))
    
    print("\n--- İstasyon Arama Testi ---")
    print(search_charging_stations.invoke({"location": "İstanbul Pendik"}))
