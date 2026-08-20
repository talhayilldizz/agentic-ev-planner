import os
from langchain_core.tools import tool
from ddgs import DDGS
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PRICE_CSV = os.path.join(DATA_DIR, "TARIFE.csv")

PRICE_DF = pd.read_csv(PRICE_CSV)

@tool
def calculate_price(
    station_name: str, 
    is_fast_charge: bool = False
) -> float:
    """
        İstasyon operatörüne göre kWh başına şarj fiyatını bulur.
        Örnek: Trugo -> DC fiyatı.
    """
    if not station_name:
        return 0.0

    if PRICE_DF.empty:
        return 0.0

    charge_type = "DC" if is_fast_charge else "AC"

    result = PRICE_DF[
        PRICE_DF["Operator"].str.lower() == station_name.lower()
    ]
    if result.empty:
        return 0.0

    price = result.iloc[0][charge_type]

    price = str(price).replace("₺", "").strip()

    return float(price)



if __name__ == "__main__":
    print(
        calculate_price.invoke({
            "station_name": "ZES",
            "is_fast_charge":False
        })
    )


    

    


    