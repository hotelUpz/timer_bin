import hmac
import hashlib
import requests
import time
import pandas as pd
import time
from decimal import Decimal

class BINANCE_API():
    def __init__(self):
        pass
    # POST ////////////////////////////////////////////////////////////////////
    def get_url_market_query(self, api_secret, symbol, side, quantity):
        base_url = "https://api.binance.com/api/v3/order"
        timestamp = int(time.time() * 1000)
        query_string = f"symbol={symbol}&side={side}&type=MARKET&quantity={quantity}&timestamp={timestamp}&recvWindow=5000"
        signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        return f"{base_url}?{query_string}&signature={signature}"

    def get_url_limit_query(self, api_secret, symbol, side, qnt, target_price):
        base_url = "https://api.binance.com/api/v3/order"
        timestamp = int(time.time() * 1000)
        query_string = f"symbol={symbol}&side={side}&type=LIMIT&quantity={qnt}&price={target_price}&timeInForce=GTC&timestamp={timestamp}"
        signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        return f"{base_url}?{query_string}&signature={signature}"

    def place_market_order(self, api_key, api_secret, symbol, side, qnt):               
        url = self.get_url_market_query(api_secret, symbol, side, qnt)            
        return requests.post(url, headers={'X-MBX-APIKEY': api_key})

    def place_limit_order(self, api_key, api_secret, symbol, side, qnt, target_price):              
        url = self.get_url_limit_query(api_secret, symbol, side, qnt, target_price)
        return requests.post(url, headers={'X-MBX-APIKEY': api_key})

    # GET /////////////////////////////////////////////////////////////////////////////////

    def get_exchange_info(self, symbol):
        url = f"https://api.binance.com/api/v3/exchangeInfo?symbol={symbol}"
        try:
            exchange_info = requests.get(url)
            return exchange_info.json()        
        except Exception as ex:
            print(ex)
            return

    def get_current_price(self, symbol):    
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        try:
            response = requests.get(url)
            data = response.json()
            return float(data["price"])
        except Exception as ex:
            print(ex)
            return

    def get_klines(self, symbol, interval='1m', limit=5):    
        url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
        try:
            response = requests.get(url)
            if response.status_code != 200:
                print(f'Failed to fetch data. Status code: {response.status_code}')
                return pd.DataFrame()
            data = response.json()
            data = pd.DataFrame(data, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTime', 'QuoteAssetVolume', 'NumberOfTrades', 'TakerBuyBaseAssetVolume', 'TakerBuyQuoteAssetVolume', 'Ignore'])
            data['Time'] = pd.to_datetime(data['Time'].astype(int), unit='ms')
            data.set_index('Time', inplace=True)
            return data.astype(float)
        except Exception as ex:
            print(ex)
            return
        
    # DELETE ///////////////////////////////////////////////////////////////////////////////////////////////
    def get_url_cancel_limit_query(self, api_secret, symbol, orderId):
        base_url = "https://api.binance.com/api/v3/order"
        timestamp = int(time.time() * 1000)
        query_string = f"symbol={symbol}&orderId={orderId}&timestamp={timestamp}"
        signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        return f"{base_url}?{query_string}&signature={signature}"

    def cancel_limit_order_by_id(self, api_key, api_secret, symbol, orderId):   
        url = 'https://api.binance.com/api/v3/order'           
        url = self.get_url_cancel_limit_query(api_secret, symbol, orderId)
        return requests.delete(url, headers={'X-MBX-APIKEY': api_key})

    # UTILS /////////////////////////////////////////////////////////////////////////////////////////////////
    def usdt_to_qnt_converter(self, symbol, depo):
        try:        
            symbol_info = self.get_exchange_info(symbol)                     
            symbol_data = next((item for item in symbol_info["symbols"] if item['symbol'] == symbol), None)     
            lot_size_filter = next((f for f in symbol_data.get('filters', []) if f.get('filterType') == 'LOT_SIZE'), None)
            step_size = str(float(lot_size_filter.get('stepSize')))      
            quantity_precision = Decimal(step_size).normalize().to_eng_string()        
            quantity_precision = len(quantity_precision.split('.')[1])  
            minNotional = float(next((f['minNotional'] for f in symbol_data['filters'] if f['filterType'] == 'NOTIONAL'), None))
            maxNotional = float(next((f['maxNotional'] for f in symbol_data['filters'] if f['filterType'] == 'NOTIONAL'), None))    
            price = self.get_current_price(symbol)
            if depo <= minNotional:
                depo = minNotional               
            elif depo >= maxNotional:
                depo = maxNotional        
            return round(depo / price, quantity_precision), quantity_precision
        except Exception as ex:
            print(ex) 
            return None, None
