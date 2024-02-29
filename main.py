import sched
import time
import telebot
from telebot import types
from api_binance import BINANCE_API
from init_params import PARAMS
from utils import UTILS
# import logging, os, inspect
# logging.basicConfig(filename='log.log', level=logging.INFO)
# current_file = os.path.basename(__file__)

class CONNECTOR_TG(PARAMS):
    def __init__(self):  
        super().__init__()                  
        self.bot = telebot.TeleBot(self.tg_api_token)
        self.menu_markup = self.create_menu()   

    def create_menu(self):
        menu_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
        button1 = types.KeyboardButton("START")
        button2 = types.KeyboardButton("SET_TIMER")
        button3 = types.KeyboardButton("SELL_ALL")
        menu_markup.add(button1, button2, button3)        
        return menu_markup

class TG_ASSISTENT(CONNECTOR_TG):
    def __init__(self):
        super().__init__()
        self.handle_sell_all_redirect = False
        self.handle_set_timer_redirect = False
        self.response_data_list = []
        self.qnt = 0

    def connector_func(self, message, response_message):
        retry_number = 3
        decimal = 1.1       
        for i in range(retry_number):
            try:
                self.bot.send_message(message.chat.id, response_message)
                # self.bot.send_message(chat_id=self.CHAT_ID, text=response_message)                            
                return message.text
            except Exception as ex:                
                time.sleep(1.1 + i*decimal)                   
        return None

class FATHER(TG_ASSISTENT, BINANCE_API, UTILS):
    def __init__(self) -> None:
        super().__init__()

    def sell_by_force(self, api_key, api_secret, symbol, sell_qnt, response_data_list, iter_list):
        for x in response_data_list:
            try: 
                if x['status'] == 'NEW':
                    orderId = x['orderId']                    
                    response_cancel_order = self.cancel_limit_order_by_id(api_key, api_secret, symbol, orderId)                    
                    response_cancel_order = response_cancel_order.json()                    
                    response_data_list.append(response_cancel_order)
                    time.sleep(0.1)
            except Exception as ex:
                print(ex)
                # logging.exception(
                #     f"An error occurred in file '{current_file}', line {inspect.currentframe().f_lineno}: {ex}") 
              
        for _ in iter_list:  
            try:            
                response = None              
                side = 'SELL'                
                response = self.place_market_order(api_key, api_secret, symbol, side, sell_qnt)
                response = response.json()
                response_data_list.append(response)                
                try:
                    if response["status"] == "FILLED":                                                          
                        break                                              
                except Exception as ex:
                    print(ex)
                    # logging.exception(
                    #     f"An error occurred in file '{current_file}', line {inspect.currentframe().f_lineno}: {ex}")                  
                time.sleep(0.1)           
            except Exception as ex:
                print(ex)
                # logging.exception(
                #     f"An error occurred in file '{current_file}', line {inspect.currentframe().f_lineno}: {ex}") 
        return response_data_list
    
    def grid_tp(self, api_key, api_secret, symbol, qnt, quantity_precision, price_precession, iter_list):    
        target_list = []
        response_data_list = []
        klines = self.get_klines(symbol)
        hight = klines['High'].iloc[-1]            
        close_price = klines['Close'].iloc[-1]
        # print(hight)            
        # print(close_price)
        print('#///////////////////////////////')
        if hight > close_price:
            addit_pices = (hight - close_price)*0.49
            target_list.append(round(close_price + addit_pices, price_precession))        
            target_list.append(round(hight * 1.1, price_precession))
            qnt = round(qnt/2, quantity_precision)
        else:
            target_list.append(round(hight * 1.2, price_precession))        
        
        for target_price in target_list:
            response_data_list += self.limit_tp_template(api_key, api_secret, symbol, qnt, target_price, iter_list)

        return response_data_list

    def limit_tp_template(self, api_key, api_secret, symbol, qnt, target_price, iter_list):  
        response_data_list = []       

        for _ in iter_list:  
            try:            
                response = None              
                side = 'SELL'                
                response = self.place_limit_order(api_key, api_secret, symbol, side, qnt, target_price)
                response = response.json()
                response_data_list.append(response)                
                try:
                    if response["status"] == "NEW":                                                              
                        break                             
                except Exception as ex:
                    print(ex)
                    # logging.exception(
                    #     f"An error occurred in file '{current_file}', line {inspect.currentframe().f_lineno}: {ex}")
                time.sleep(0.1)                   
            
            except Exception as ex:
                print(ex)
                # logging.exception(
                #     f"An error occurred in file '{current_file}', line {inspect.currentframe().f_lineno}: {ex}")

        return response_data_list

    def strategy(self, api_key, api_secret, symbol, depo, tp_rate, tp_mode, false_start_deprecator, iter_list, message):        
        response_success_list = []   
        for _ in iter_list:  
            try:            
                response = None              
                # if i == 1:            
                #     time.sleep(false_start_deprecator)
                side = 'BUY'
                buy_qnt, quantity_precision = self.usdt_to_qnt_converter(symbol, depo)
                response = self.place_market_order(api_key, api_secret, symbol, side, buy_qnt)
                response = response.json()
                self.response_data_list.append(response)                
                try:
                    if response["status"] == "FILLED": 
                        response_success_list.append(response)                                   
                        break  
                    time.sleep(0.1)                           
                except Exception as ex:
                    print(ex)
                    # logging.exception(
                    #     f"An error occurred in file '{current_file}', line {inspect.currentframe().f_lineno}: {ex}")                  
                    if response["code"] == -1121: 
                        time.sleep(0.1)                           
                        continue
                    break                
            except Exception as ex:
                print(ex)
                # logging.exception(
                #     f"An error occurred in file '{current_file}', line {inspect.currentframe().f_lineno}: {ex}") 
        if len(response_success_list) != 0:            
            enter_price = 0 
            self.qnt = float(response_success_list[0]["fills"][0]["qty"])
            enter_price = float(response_success_list[0]["fills"][0]["price"])
            price_precession = self.price_precession_extractor(enter_price)
            
            if tp_mode == 'fixed':
                target_price = round(enter_price* tp_rate, price_precession)
                self.response_data_list += self.limit_tp_template(api_key, api_secret, symbol, self.qnt, target_price, iter_list)
            else:
                self.response_data_list += self.grid_tp(api_key, api_secret, symbol, self.qnt, quantity_precision, price_precession, iter_list)                
            
            tg_connector_resp = self.connector_func(message, str(self.response_data_list) + '\n' + 'Almost done!')            
            print('Almost done!')
        else:
            print('Some problems with placing buy market order...')

    def schedule_order_execution(self, target_time, api_key, api_secret, symbol, depo, tp_rate, tp_mode, false_start_deprecator, iter_list, message): 
        try:    
            scheduler = sched.scheduler(time.time, time.sleep)
            scheduler.enterabs(time.mktime(time.strptime(target_time, "%Y-%m-%d %H:%M:%S")), 1, self.strategy, argument=(api_key, api_secret, symbol, depo, tp_rate, tp_mode, false_start_deprecator, iter_list, message))
            scheduler.run()
        except Exception as ex:
            print(ex)

    def run_father(self, message):   
        print('God blass you Nik!')
        try:
            tg_connector_resp = self.connector_func(message, 'God blass you Nik!')
            respons_mess = 'There are the next default timer options:' + '\n'
            respons_mess += self.symbol + '\n'
            respons_mess += str(self.depo) + '\n'
            respons_mess += str(self.tp_rate) + '\n'
            respons_mess += self.tp_mode + '\n'
            respons_mess += self.order_time + '\n'        
            connector_resp = self.connector_func(message, respons_mess)                     
            self.schedule_order_execution(self.order_time, self.api_key, self.api_secret, self.symbol, self.depo, self.tp_rate, self.tp_mode, self.false_start_deprecator, self.iter_list, message)
        except Exception as ex:
            print(ex)

class TG_MANAGER(FATHER):
    def __init__(self):
        super().__init__()
        
    def run_tg_bot(self):
        @self.bot.message_handler(commands=['start'])
        @self.bot.message_handler(func=lambda message: message.text == 'START')
        def handle_start_input(message):
            print('hello1')                 
            self.run_father(message)

        # //////////////////////////////////////////////////////////////////////////////////////
        @self.bot.message_handler(func=lambda message: message.text == 'SET_TIMER')
        def handle_set_timer_input(message):
            connector_resp = self.connector_func(message, "Please enter a timer options: symbol depo tp_rate tp_mode order_time using spaces (e.g: portalfdusd 401 1.23 fixed 2024-02-29/01:58:00 or portalusdt 401 1.23 g 2024-02-29/01:58:00)")
            self.handle_set_timer_redirect = True

        @self.bot.message_handler(func=lambda message: self.handle_set_timer_redirect)
        def handle_set_timer_input(message):
            try:
                self.handle_set_timer_redirect = False                
                respons_mess = 'The timer options was changed:' + '\n'
                dataa = message.text.strip().split(' ')
                dataa = [x for x in dataa if x !=' ']
                self.symbol = dataa[0].strip().upper()
                respons_mess += self.symbol + '\n'
                self.depo = float(dataa[1].strip())
                respons_mess += str(self.depo) + '\n'
                self.tp_rate = float(dataa[2].strip())
                respons_mess += str(self.tp_rate) + '\n'
                self.tp_mode = dataa[3].strip()
                respons_mess += self.tp_mode + '\n'
                self.order_time = dataa[4].strip().replace('/', ' ')
                respons_mess += self.order_time + '\n'                       
                connector_resp = self.connector_func(message, respons_mess)
            except Exception as ex:
                print(ex)
        # //////////////////////////////////////////////////////////////////////////////////////
        @self.bot.message_handler(func=lambda message: message.text == 'SELL_ALL')
        def handle_sell_all_input(message):
            sell_force_var = self.connector_func(message, "Are you sure you want to sell all? (y/n)")
            self.handle_sell_all_redirect = True

        @self.bot.message_handler(func=lambda message: self.handle_sell_all_redirect)
        def handle_sell_all_redirect(message):
            self.handle_sell_all_redirect = False
            sell_force_var = message.text.strip().upper() == 'N'            
            if sell_force_var:
                print('Sell by force was deprecated')
                sell_force_var = self.connector_func(message, "Sell by force was deprecated")
            else:
                # print(self.qnt)
                self.response_data_list = self.sell_by_force(self.api_key, self.api_secret, self.symbol, self.qnt, self.response_data_list, self.iter_list)                
                tg_connector_resp = self.connector_func(message, str(self.response_data_list))  
                print(self.response_data_list)
            result_time = self.show_trade_time(self.response_data_list)
            tg_connector_resp = self.connector_func(message, result_time + '\n' + 'Congratulations!')
            self.response_data_list = []
            print(self.SOLI_DEO_GLORIA)     
        # ////////////////////////////////////////////////////////////////////////////////////// 
        try:          
            self.bot.infinity_polling()
        except Exception as ex:
            print(ex)
        
def main():   
    father = TG_MANAGER()  
    father.run_tg_bot()  

if __name__=="__main__":
    main()
