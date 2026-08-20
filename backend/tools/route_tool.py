from langchain_core.tools import tool
import requests
import math
import sqlite3
import os
import json
from tools.price_tool import calculate_price

def haversine(lat1, lon1, lat2, lon2):
    """İki GPS koordinatı arasındaki kuş uçuşu mesafeyi (km) hesaplar."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def geocode_city(city_name: str):
    """Şehir ismini koordinata çevirir."""
    url = f"https://nominatim.openstreetmap.org/search?q={city_name},Turkey&format=json&limit=1"
    response = requests.get(url, headers={'User-Agent': 'EVRoutePlanner/1.0'})
    if response.status_code == 200 and response.json():
        return float(response.json()[0]['lat']), float(response.json()[0]['lon'])
    return None, None

@tool
def plan_smart_ev_route(
    start_city: str, 
    end_city: str, 
    battery_capacity_kwh: float,
    current_charge_percent: float,
    consumption_kwh_per_100km: float
) -> str:
    """
    Başlangıç ve bitiş şehirleri arasında gerçek GPS rotasını çizer, toplam mesafeyi bulur.
    Şarjın nerelerde biteceğini hesaplayıp zincirleme (çoklu) şarj durakları oluşturur.
    """
    try:
        lat1, lon1 = geocode_city(start_city)
        lat2, lon2 = geocode_city(end_city)
        if not lat1 or not lat2: return "Şehir koordinatları bulunamadı."
            

        current_energy = battery_capacity_kwh * (current_charge_percent / 100.0)
        
        
        theoretical_initial_range = (current_energy / consumption_kwh_per_100km) * 100.0
        theoretical_full_range = (battery_capacity_kwh / consumption_kwh_per_100km) * 100.0
        
       
        REAL_WORLD_FACTOR = 0.80
        
        initial_range = theoretical_initial_range * REAL_WORLD_FACTOR
        full_range = theoretical_full_range * REAL_WORLD_FACTOR

        # OSRM ile rotayı al
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        response = requests.get(url)
        if response.status_code != 200 or response.json().get('code') != 'Ok':
            return "Rota çizilemedi."
            
        data = response.json()
        coordinates = data['routes'][0]['geometry']['coordinates']
        total_distance_km = data['routes'][0]['distance'] / 1000.0
        
        if initial_range >= total_distance_km:
            return f"✅ **Harika!** {start_city} - {end_city} arası {total_distance_km:.1f} km. Mevcut şarjınız ({initial_range:.1f} km) durmaksızın gitmek için yeterli."
            
        
        stop_distances = []
        current_km = initial_range * 0.90 
        while current_km < total_distance_km:
            stop_distances.append(current_km)
            current_km += full_range * 0.90 
            
        
        stop_points = []
        acc_dist = 0.0
        stop_idx = 0
        for i in range(len(coordinates) - 1):
            p1, p2 = coordinates[i], coordinates[i+1]
            dist = haversine(p1[1], p1[0], p2[1], p2[0])
            while stop_idx < len(stop_distances) and acc_dist + dist >= stop_distances[stop_idx]:
                stop_points.append((p2[1], p2[0]))
                stop_idx += 1
            acc_dist += dist
            
        
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'ev_database.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT brand, province, district, socket_count, max_power_kw, connector_type, latitude, longitude FROM charging_stations WHERE latitude IS NOT NULL")
        stations = cursor.fetchall()
        conn.close()

        map_data = {
            "type": "ev_route_map",
            "start": [lat1, lon1],
            "end": [lat2, lon2],
            "stops": []
        }

        
        output = f"🚗 **Rota Planı:** {start_city.title()} ➡️ {end_city.title()} (Toplam: {total_distance_km:.1f} km)\n"
        output += f"⚠️ Yol boyunca toplam **{len(stop_points)} kez** şarj molası vermeniz gerekiyor.\n\n"

        previous_distance = 0.0
        total_charge_energy = 0.0
        total_cost_tl = 0.0
        
        for i, point in enumerate(stop_points):
            stop_lat, stop_lon = point
            
            
            closest_station = None
            min_dist = float('inf')
            for s in stations:
                d = haversine(stop_lat, stop_lon, s['latitude'], s['longitude'])
                if d < min_dist:
                    min_dist = d
                    closest_station = s
                    
            s = closest_station

            real_consumption = consumption_kwh_per_100km / REAL_WORLD_FACTOR
            
            leg_distance = stop_distances[i] - previous_distance
            energy_used = (leg_distance * real_consumption) / 100.0

            energy_remaining = current_energy - energy_used
            energy_remaining = max(0, energy_remaining)

            if i + 1 < len(stop_distances):
                next_stop_distance = stop_distances[i + 1] - stop_distances[i]
            else:
                next_stop_distance = total_distance_km - stop_distances[i]

            energy_needed_next_leg = (next_stop_distance * real_consumption) / 100.0

            reserve_energy = battery_capacity_kwh * 0.10 # %10 Güvenlik Payı
            target_energy = energy_needed_next_leg + reserve_energy
            
            charge_needed = target_energy - energy_remaining
            charge_needed = max(0, charge_needed)
            max_charge_possible = battery_capacity_kwh - energy_remaining
            charge_needed = min(charge_needed, max_charge_possible)

            energy_after_charge = energy_remaining + charge_needed
            charge_after_percent = (energy_after_charge / battery_capacity_kwh) * 100.0
            
            total_charge_energy += charge_needed

            if s["max_power_kw"] and s["max_power_kw"] > 0:
                avg_power = s["max_power_kw"] * 0.8 
                charging_time_minutes = (charge_needed / avg_power) * 60
            else:
                charging_time_minutes = 0

            is_fast_charge = s["max_power_kw"] and s["max_power_kw"] >= 22
            try:
                price_per_kwh = float(calculate_price.invoke({
                    "station_name": s["brand"],
                    "is_fast_charge": is_fast_charge
                }))
                if not price_per_kwh or price_per_kwh <= 0:
                    price_per_kwh = 10.0
            except:
                price_per_kwh = 10.0
            
            leg_cost = charge_needed * price_per_kwh
            total_cost_tl += leg_cost

            maps_link = f"https://www.google.com/maps/search/?api=1&query={s['latitude']},{s['longitude']}"
            output += f"🔌 **{i+1}. Mola Noktası ({stop_distances[i]:.1f}. Kilometre):**\n"
            output += f"- 📍 Bölge: {s['province']} - {s['district']} civarı\n"
            output += f"- ⚡ İstasyon: {s['brand']} ({s['max_power_kw']} kW Max, {s['socket_count']} Soket)\n"
            output += f"- 🔋 İstasyona varış enerjisi: **{energy_remaining:.1f} kWh**\n"
            output += f"- ⚡ Gerekli şarj: **{charge_needed:.1f} kWh**\n"
            output += f"- 💰 Birim Fiyat: **{price_per_kwh:.2f} ₺/kWh** (Durak Maliyeti: {leg_cost:.2f} ₺)\n"
            output += f"- 🔋 Şarj sonrası: **{energy_after_charge:.1f} kWh ({charge_after_percent:.0f}%)**\n"
            output += f"- ⏱️ Tahmini şarj süresi: **{charging_time_minutes:.0f} dakika**\n"
            output += f"- 🗺️ [İstasyona Gitmek İçin Tıkla]({maps_link})\n\n"
            map_data["stops"].append({
                "lat": s["latitude"],
                "lon": s['longitude'],
                "title": f"{s['brand']} ({s['province']})",
                "popup":f"{s['max_power_kw']} kW Max - {s['socket_count']} Soket",
                "maps_link": maps_link
            })

            current_energy = energy_after_charge
            previous_distance = stop_distances[i]


        output += f"🔋 **Toplam alınacak enerji:** {total_charge_energy:.1f} kWh\n"
        
        output += f"💰 **Tahmini Toplam Şarj Maliyeti:** {total_cost_tl:.2f} ₺\n"
        
        output += "*(Hesaplamalarda gerçek dünya koşulları (%20 kayıp) ve %10 güvenlik payı baz alınmıştır.)*"
        
        output += f"\n\n```json\n{json.dumps(map_data, ensure_ascii=False, indent=2)}\n```"
        return output
    except Exception as e:
        return f"Planlama hatası: {str(e)}"
