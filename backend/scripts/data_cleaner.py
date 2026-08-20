import pandas as pd
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
DATA_DIR = os.path.join(BASE_DIR, 'data')

VEHICLES_CSV = os.path.join(DATA_DIR, 'electric_vehicles_spec_2025.csv.csv')
STATIONS_CSV = os.path.join(DATA_DIR, 'ev_charging_stations_turkey.csv')
DB_PATH = os.path.join(DATA_DIR, 'ev_database.db')

def clean_column_names(df):
    df.columns = df.columns.str.strip().str.lower()
    df.columns = df.columns.str.replace(r'[^a-zA-Z0-9]', '_', regex=True)
    df.columns = df.columns.str.replace(r'_+', '_', regex=True)
    df.columns = df.columns.str.strip('_')
    return df

def run_data_pipeline():
    print("Veri temizleme ve SQLite aktarım işlemi başlatılıyor...")
    
    print(f"[{VEHICLES_CSV}] yükleniyor...")
    df_vehicles = pd.read_csv(VEHICLES_CSV, encoding='utf-8')
    df_vehicles = clean_column_names(df_vehicles)
    df_vehicles.dropna(how='all', inplace=True)
    
    
    keep_vehicle_cols = [
        'brand', 'model', 'battery_capacity_kwh', 'range_km', 
        'fast_charging_power_kw_dc', 'efficiency_wh_per_km'
    ]
    actual_vehicle_cols = [c for c in keep_vehicle_cols if c in df_vehicles.columns]
    df_vehicles = df_vehicles[actual_vehicle_cols]
    print(f"Araç verisi filtrelendi. Toplam Satır: {len(df_vehicles)}")

    print(f"[{STATIONS_CSV}] yükleniyor...")
    df_stations = pd.read_csv(STATIONS_CSV, encoding='utf-8')
    df_stations = clean_column_names(df_stations)
    df_stations.dropna(how='all', inplace=True)
    
    df_grouped = df_stations.groupby(
        ['station_id', 'brand', 'province', 'district'], 
        as_index=False
    ).agg({
        'socket_id': 'count',      
        'power_kw': 'max',         
        'connector_type': lambda x: ', '.join(set(x.dropna().astype(str))),
        'latitude': 'first',   
        'longitude': 'first'   
    })
    
    df_grouped.rename(columns={'socket_id': 'socket_count', 'power_kw': 'max_power_kw'}, inplace=True)
    print(f"İstasyon verisi gruplandı (Soket -> İstasyon). Toplam İstasyon: {len(df_grouped)}")
   
    
    print(f"SQLite veritabanı oluşturuluyor: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    df_vehicles.to_sql('vehicles', conn, if_exists='replace', index=False)
    df_grouped.to_sql('charging_stations', conn, if_exists='replace', index=False)
    conn.close()
    
    print("İşlem başarıyla tamamlandı! Veriler 'ev_database.db' dosyasına güncellendi.")

if __name__ == "__main__":
    run_data_pipeline()
