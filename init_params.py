import os
from dotenv import load_dotenv
load_dotenv()

class PARAMS():
    def __init__(self) -> None:
        self.init_keys()
        self.SOLI_DEO_GLORIA = 'Soli Deo Gloria!'
        self.symbol = 'ARBUSDT'
        self.depo = 12
        self.tp_rate = 1.23
        self.tp_mode = 'fixed' # 'fixed'
        self.order_time = "2024-02-29 02:43:00" # "2024-02-29 12:00:00", PORTAL
        # //////////////////////////////////////////////////////////////////////
        self.false_start_deprecator = 0 
        attempts_number = 3        
        self.iter_list = list(range(1, attempts_number + 1))  
    
    def init_keys(self):
        self.tg_api_token = os.getenv("TG_API_TOKEN", "")
        self.api_key  = os.getenv(f"BINANCE_API_PUBLIC_KEY", "")
        self.api_secret = os.getenv(f"BINANCE_API_PRIVATE_KEY", "") 



         