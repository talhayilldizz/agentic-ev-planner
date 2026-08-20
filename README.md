# Agentic EV Route Planner

Bu proje, yapay zeka (LangGraph & GPT-4o-mini) destekli bir Elektrikli Arac (EV) Rota Planlayicisidir. Kullanicinin verdigi araba modeline gore menzil hesaplar, guzergah uzerindeki en ideal sarj molalarini bulur ve gercek dunya fiyatlandirmalariyla rotayi harita uzerinde cizer.

## Mimari Yapi (Agent & LangGraph)

Sistem ReAct (Reason + Act) mimarisi uzerine kurulmustur. Yapay zeka, kendisine verilen gorevleri Python araclarina delege ederek sonuc uretir. Asagida sistemin calisma semasi verilmistir:

```text
       [ KULLANICI ]
             |
             v (1. Frontend: Ihtiyac ve Istek)
 +-----------------------+
 |   React + Vite Arayuz | (Harita Cizimi ve Markdown Okuma)
 +-----------------------+
             |
             v (2. POST /chat HTTP Istegi)
 +-----------------------+
 |      FastAPI (API)    | <-- (En son burada JSON Harita verisi zorla mesaja eklenir)
 +-----------+-----------+
             |
             v (3. graph.stream baslatilir)
 +====================================================================+
 |                     LANGGRAPH (Orkestrasyon)                       |
 |                                                                    |
 |                      +-------------------+                         |
 |    (4) Karar Ver <-- |   AGENT (Dugum)   | <-+                     |
 |                      |  (GPT-4o-mini)    |   |                     |
 |                      +-------------------+   | (Dongu)             |
 |                        |      ^              |                     |
 |        (Arac Cagrisi)  |      |              |                     |
 |                        v      | (Arac Yaniti)|                     |
 |                      +-------------------+   |                     |
 |                      |   TOOLS (Dugum)   |---+                     |
 |                      | (Python Araclari) |                         |
 |                      +-------+-----------+                         |
 |                              |                                     |
 |         +----------------+---------------+-----------------+------------------+---------------+
 |         v                v               v                 v                  v               |
 |  [search_vehicle] [plan_ev_route] [calculate_price] [calc_energy_cons]   [web_search]         |
 |  (db_tool.py)     (route_tool.py) (price_tool.py)   (calc_tool.py)       (web_tool.py)        |
 |         |                |               |                 |                  |               |
 |         v                v               v                 v                  v               |
 | SQLite (Arac DB)  OSRM API / Harita  TARIFE.csv        Matematik         DuckDuckGo (Web)     |
 +===============================================================================================+
             |
             v (5. Ajan "Cevap Hazir" der ve donguden cikar)
      FastAPI'ye Doner
```

## Ozellikler
- Arac Arama: Veritabanindan menzil, tuketim kapasitesi cekme.
- Gercek Dunya Tuketimi: Fabrika verisine kayip carpani uygulayarak menzil daraltma ve guncel tuketim hesaplama.
- Durak Hesaplama: Aractaki sarj durumuna ve menzil guvenlik payina gore mola planlama. En yakin istasyonlari Haversine formulu ile tespit etme.
- Harita Cizimi: Mola duraklari ve kesisim yollarini OSRM ile cizip React Leaflet uzerinde interaktif gosterme.
- Dinamik Maliyet: Istasyonun markasina, DC/AC tipine gore TARIFE.csv uzerinden anlik sarj fiyatlandirmasi cikartma.

## Kurulum ve Calistirma

Projede sarj istasyonlari ve araba modellerinin veritabani dosyasi boyutu geregi (ev_database.db) GitHub'a yuklenmemistir. Projeyi bilgisayariniza ilk indirdiginizde veritabanini olusturmaniz gerekir.

### 1. Adim: Veritabanini Olusturun
Proje klasorundeki ham Excel ve CSV dosyalarini (TARIFE.csv, istasyon verileri vb.) okuyup .db dosyasini olusturmak icin veri temizleme betigini calistirin:
```bash
# Proje kok dizinindeyken
cd backend
python scripts/data_cleaner.py
```
Bu komut, backend/data/ev_database.db dosyasini otomatik olarak olusturacaktir.

### 2. Adim: Cevresel Degiskenleri Ayarlayin
Ana dizindeki .env.example dosyasinin adini .env olarak degistirin ve icine kendi OpenAI anahtarinizi yazin:
```text
OPENAI_API_KEY="sk-..."
```

### 3. Adim: Projeyi Ayaga Kaldirin (Docker)
Docker kullanarak hem backend (FastAPI) hem de frontend (React) sunucularini tek komutla calistirabilirsiniz:
```bash
docker-compose up -d
```

Uygulama calistiktan sonra tarayicinizdan localhost uzerinden projeye ulasabilirsiniz.

## Veri Kaynaklari (Datasets)

Bu projenin altyapisinda kullanilan gercek dunya verileri asagidaki Kaggle veri setlerinden derlenmistir:

- [Electric Vehicle Specifications Dataset 2025](https://www.kaggle.com/datasets/urvishahir/electric-vehicle-specifications-dataset-2025): Elektrikli araclarin batarya, menzil ve tuketim verileri.
- [Turkey EV Charging Stations Network Geospatial](https://www.kaggle.com/datasets/aliemirkoca/turkey-ev-charging-stations-network-geospatial): Turkiye'deki sarj istasyonlarinin koordinat, marka ve kapasite bilgileri.
