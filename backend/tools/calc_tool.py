from langchain_core.tools import tool

@tool
def calculate_energy_consumption(
    battery_capacity_kwh: float,
    current_charge_percent: float,
    consumption_kwh_per_100km: float, 
    average_speed_kmh: float = 90.0
) -> str:
    """
    Kullanıcının mevcut şarj yüzdesi, batarya kapasitesi ve tüketim verisine göre
    kalan menzilini (km) ve bu menzilin kaç saat/dakika süreceğini hesaplar.
    
    Argümanlar:
    - battery_capacity_kwh: Aracın toplam batarya kapasitesi (kWh). (Kullanıcı aracı söylediyse önce search_vehicle ile kapasiteyi bul)
    - current_charge_percent: Aracın şu anki şarj yüzdesi (Örn: %80 ise 80 girin).
    - consumption_kwh_per_100km: 100 km'deki enerji tüketimi (kWh).
    - average_speed_kmh: Ortalama hız (km/s). Varsayılan: 90.0
    """

    try:
        current_energy_kwh = battery_capacity_kwh * (current_charge_percent / 100.0)

        if consumption_kwh_per_100km <= 0:
            return "Tüketim değeri 0'dan büyük olmalıdır."
        
        range_km = (current_energy_kwh / consumption_kwh_per_100km) * 100.0

        time_hours = range_km / average_speed_kmh
        hours = int(time_hours)
        minutes = int((time_hours - hours) * 60)
        
        return (
            f"✅ **Hesaplama Sonucu:**\n"
            f"- Kalan Enerji: {current_energy_kwh:.1f} kWh\n"
            f"- Tahmini Menzil: {range_km:.1f} km\n"
            f"- {average_speed_kmh} km/s hızla sürüş süresi: {hours} saat {minutes} dakika"
        )

    except Exception as e:
        return f"Hesaplama hatası: {str(e)}"