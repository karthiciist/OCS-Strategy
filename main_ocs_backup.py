import requests
import pandas as pd
import time
import datetime
import numpy as np
from ta.trend import ADXIndicator
import yfinance as yf
from fyers_api import accessToken, fyersModel
from stockstats import StockDataFrame
import math
import pyodbc


def time_in_range(start, end, current):
    """Returns whether current is in the range [start, end]"""
    return start <= current <= end


def is_it_trade_time():
    start_first_time_window = datetime.time(9, 25, 0)
    end_first_time_window = datetime.time(22, 45, 0)
    current_first_time_window = datetime.datetime.now().time()
    first_time_window = time_in_range(start_first_time_window, end_first_time_window, current_first_time_window)
    if first_time_window == False:
        start_second_time_window = datetime.time(12, 45, 0)
        end_second_time_window = datetime.time(14, 30, 0)
        current_second_time_window = datetime.datetime.now().time()
        second_time_window = time_in_range(start_second_time_window, end_second_time_window, current_second_time_window)

    if first_time_window:
#         print ("Time is morning trade time")
        return True
    elif second_time_window:
#         print ("Time is noon trade time")
        return True
    else:
#         print ("Not a trade time")
        return False


# def get_history():
#     clientid = "RVLYRDO3H5-100"
#     access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGkuZnllcnMuaW4iLCJpYXQiOjE2ODkzMDg4ODgsImV4cCI6MTY4OTM4MTAwOCwibmJmIjoxNjg5MzA4ODg4LCJhdWQiOlsieDowIiwieDoxIiwieDoyIiwiZDoxIiwiZDoyIiwieDoxIiwieDowIl0sInN1YiI6ImFjY2Vzc190b2tlbiIsImF0X2hhc2giOiJnQUFBQUFCa3NNN1kxNzlaZGlTLVRYNmpWQXFnQmpTUjdOdlNXNmF4UGNOQlgxREZiTXpfcHdfUUxRY0x3UFh2WGhkazg3U1lGdlNQbkJwQWRodGVNQkJjZDl2aGVlYTlDZ3VzN21XMXVoQUJiMjI2NGdwSGp3MD0iLCJkaXNwbGF5X25hbWUiOiJERUVOQURIQVlBTEFOIEtBUlRISSBTUklOSVZBU0FOIiwib21zIjoiSzEiLCJmeV9pZCI6IlhEMjA3ODkiLCJhcHBUeXBlIjoxMDAsInBvYV9mbGFnIjoiTiJ9.QVQw0PzXcK_oubv2T67zvc-z7ac-KqvY-32WGgpKivQ"
#
#     fyers = fyersModel.FyersModel(client_id=clientid, token=access_token)
#
#     data = {
#         "symbol": "NSE:NIFTY50-INDEX",
#         "resolution": "1",
#         "date_format": "1",
#         "range_from": "2023-07-05",
#         "range_to": "2023-07-14",
#         "cont_flag": "1"
#     }
#
#     response = fyers.history(data=data)
#     #     print(response)
#     return response


def get_option_chain_dataframe(symbol):
    url = 'https://www.nseindia.com/api/option-chain-indices?symbol=' + symbol

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36 Edg/103.0.1264.37',
        'accept-encoding': 'gzip, deflate, br', 'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8'}

    session = requests.Session()
    request = session.get(url, headers=headers)
    cookies = dict(request.cookies)

    response = session.get(url, headers=headers, cookies=cookies).json()
    rawdata = pd.DataFrame(response)
    rawop = pd.DataFrame(rawdata['filtered']['data']).fillna(0)
    data = []
    for i in range(0, len(rawop)):
        calloi = callcoi = cltp = putoi = putcoi = pltp = 0
        stp = rawop['strikePrice'][i]
        if (rawop['CE'][i] == 0):
            calloi = callcoi = 0
        else:
            calloi = rawop['CE'][i]['openInterest']
            callcoi = rawop['CE'][i]['changeinOpenInterest']
            cltp = rawop['CE'][i]['lastPrice']
        if (rawop['PE'][i] == 0):
            putoi = putcoi = 0
        else:
            putoi = rawop['PE'][i]['openInterest']
            putcoi = rawop['PE'][i]['changeinOpenInterest']
            pltp = rawop['PE'][i]['lastPrice']
        opdata = {
            #             'CALL OI': calloi, 'CALL CHNG OI': callcoi, 'CALL LTP': cltp, 'STRIKE PRICE': stp,
            #             'PUT OI': putoi, 'PUT CHNG OI': putcoi, 'PUT LTP': pltp
            'CALL LTP': cltp, 'STRIKE PRICE': stp, 'PUT LTP': pltp
        }

        data.append(opdata)
    optionchain = pd.DataFrame(data)
    return optionchain


# def find_hammer_candles(symbol):
#     # Download data for the symbol with a 1-minute interval
#     data = yf.download(symbol, interval="1m")
#     hammer_candles_list = []
#     for i in range(1, len(data)):
#         # Calculate candle attributes
#         open_price = data["Open"][i]
#         high = data["High"][i]
#         low = data["Low"][i]
#         close = data["Close"][i]
#         body_range = abs(open_price - close)
#         upper_shadow = high - max(open_price, close)
#         lower_shadow = min(open_price, close) - low
#
#         # if lower_shadow >= 2 * body_range and upper_shadow <= 0.1 * body_range:
#         #     hammer_candles_list.append(data.index[i])
#         if (float(upper_shadow) <= 1.5) and (float(low) < float(open_price)) and (float(close) > float(open_price)):
#             hammer_candles_list.append(data.index[i])
#     #             print(f"Hammer candle found at {data.index[i]}")
#     #     print(hammer_candles_list)
#     return hammer_candles_list

def find_hammer_candles(symbol, current_smma):
    # Download data for the symbol with a 1-minute interval
    #     data = yf.download(symbol, interval="1m")
    hammer_candles_list = []
    history = get_history(symbol)
    data = pd.DataFrame(history['candles'], columns=['epoch', 'open', 'high', 'low', 'close', 'volume'])
    #     print(data)
    for i in range(1, len(data)):
        # Calculate candle attributes
        epoch = data["epoch"]
        open_price = data["open"][i]
        high = data["high"][i]
        low = data["low"][i]
        close = data["close"][i]
        body_range = abs(open_price - close)
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low

        #         print (open_price, high, low, close)

        #         if lower_shadow >= 2 * body_range and upper_shadow <= 0.1 * body_range:
        #             print(f"Hammer candle found at {data.index[i]}")

        if (float(upper_shadow) <= 1.5) and (float(low) < float(open_price)) and (float(close) > float(open_price)) and (float(close) > float(current_smma) and (float(low) > float(current_smma))):
            hammer_candles_list.append(datetime.datetime.fromtimestamp(epoch[i]))
            # print(f"Hammer candle found at {datetime.datetime.fromtimestamp(epoch[i])}")
    # print(hammer_candles_list)
    return hammer_candles_list


def get_history(symbol):
    clientid = "RVLYRDO3H5-100"
    access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGkuZnllcnMuaW4iLCJpYXQiOjE2ODkzNDMzMTgsImV4cCI6MTY4OTM4MTA1OCwibmJmIjoxNjg5MzQzMzE4LCJhdWQiOlsieDowIiwieDoxIiwieDoyIiwiZDoxIiwiZDoyIiwieDoxIiwieDowIl0sInN1YiI6ImFjY2Vzc190b2tlbiIsImF0X2hhc2giOiJnQUFBQUFCa3NWVldUU3hTaFhRbGJtTVpjejQyNjRRSjhHd1ZWRk9QWW9JaWlVVExRX3dUVnVScHhYRVJSbDJ5UHFDNjZhb3FOWERZTDBmRDJaSXhDZFBPMmluUFRLWTVZdWY3NklBOVgyY2ZTeXJLNVZXb1hJND0iLCJkaXNwbGF5X25hbWUiOiJERUVOQURIQVlBTEFOIEtBUlRISSBTUklOSVZBU0FOIiwib21zIjoiSzEiLCJmeV9pZCI6IlhEMjA3ODkiLCJhcHBUeXBlIjoxMDAsInBvYV9mbGFnIjoiTiJ9.7yrxIg28idFQUUaRBIh2YiJHviKGEP-G3T6gY4XMusg"
    fyers = fyersModel.FyersModel(client_id=clientid, token=access_token)
    today = time.strftime("%Y-%m-%d")
    data = {
        "symbol": symbol,
        "resolution": "1",
        "date_format": "1",
        "range_from": "2023-07-05",
        "range_to": today,
        "cont_flag": "1"
    }

    response = fyers.history(data=data)
#     print(response)
    return response


def get_time_difference(now_time, last_candle_formed_time):
    t1 = datetime.datetime.strptime(str(last_candle_formed_time.replace(tzinfo=None)), "%Y-%m-%d %H:%M:%S")
    t2 = datetime.datetime.strptime(str(now_time), "%Y-%m-%d %H:%M:%S")
    delta = t2 - t1
    return delta.total_seconds()


def get_adx_value():
    try:
        # Download Nifty index data for a 1-minute timeframe
        nifty_data = yf.download("^NSEI", interval="1m")

        # Extract the high, low, close prices
        high = nifty_data["High"]
        low = nifty_data["Low"]
        close = nifty_data["Close"]

        # Calculate the ADX
        adx_indicator = ADXIndicator(high, low, close, window=14)
        adx = adx_indicator.adx()

        # Get last value from adx series
        last_adx = adx.iloc[-1]

        # Print the ADX values
        print(last_adx)

        return last_adx
    except Exception as e:
        print (e)


def update_db(dict_to_db):
    symbol = dict_to_db.get('symbol')
    timestamp = dict_to_db.get('timestamp')
    is_trade_time = dict_to_db.get('is_trade_time')
    close_20_sma = dict_to_db.get('close_20_sma')
    close_7_smma = dict_to_db.get('close_7_smma')
    close_9_ema = dict_to_db.get('close_9_ema')
    current_price = dict_to_db.get('current_price')
    current_ema9_price = dict_to_db.get('current_ema9_price')
    call_or_put = dict_to_db.get('call_or_put')
    strike_price = dict_to_db.get('strike_price')
    smma_greater_than_sma = dict_to_db.get('smma_greater_than_sma')
    hammer_formed = dict_to_db.get('hammer_formed')
    adx_value = dict_to_db.get('adx_value')
    buy_signal = dict_to_db.get('buy_signal')

    conn = pyodbc.connect('Driver={SQL Server Native Client 11.0};'
                          r'Server=localhost\MSSQLSERVER01;'
                          'Database=algotrade;'
                          'Trusted_Connection=yes;')  # integrated security

    cursor = conn.cursor()

    SQLCommand = (
        "INSERT INTO OCSRuntimeLogs (symbol, timestamp, is_trade_time, close_20_sma, close_7_smma, close_9_ema, current_price, current_ema9_price, call_or_put, strike_price, smma_greater_than_sma, hammer_formed, adx_value, buy_signal) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?);")
    Values = [symbol, timestamp, is_trade_time, close_20_sma, close_7_smma, close_9_ema, current_price,
              current_ema9_price, call_or_put, strike_price, smma_greater_than_sma, hammer_formed, adx_value,
              buy_signal]
    print(SQLCommand)
    # Processing Query
    cursor.execute(SQLCommand, Values)

    conn.commit()
    print("Data Successfully Inserted")
    conn.close()


def generate_expiry_dates(year):
    holidays = [
        "26-01-2023",
        "07-03-2023",
        "30-03-2023",
        "04-04-2023",
        "07-04-2023",
        "14-04-2023",
        "01-05-2023",
        "28-06-2023",
        "15-08-2023",
        "19-09-2023",
        "02-10-2023",
        "24-10-2023",
        "14-11-2023",
        "27-11-2023",
        "25-12-2023",
    ]

    holidays = [datetime.datetime.strptime(h, "%d-%m-%Y") for h in holidays]
    expiry_dates = []
    start_date = datetime.datetime(year, 1, 1)
    end_date = datetime.datetime(year, 12, 31)

    while start_date.weekday() != 3:  # Find the first Thursday of the year
        start_date += datetime.timedelta(days=1)

    while start_date <= end_date:
        if start_date not in holidays:
            expiry_dates.append(start_date.strftime("%d-%m-%Y"))
        else:  # If Thursday is a holiday, use the previous trading day as expiry day
            adjusted_expiry_date = start_date - datetime.timedelta(days=1)
            while adjusted_expiry_date in holidays:
                adjusted_expiry_date -= datetime.timedelta(days=1)
            expiry_dates.append(adjusted_expiry_date.strftime("%d-%m-%Y"))
        start_date += datetime.timedelta(weeks=1)

    return expiry_dates


def get_next_expiry():
    expiry_dates_list = generate_expiry_dates(2023)
    # print(expiry_dates_list)

    today = time.strftime("%d-%m-%Y")
    #     print(today)
    expiry_date_object_list = []
    for expiry_date in expiry_dates_list:
        expiry_date_object = datetime.datetime.strptime(expiry_date, '%d-%m-%Y')
        expiry_date_object_list.append(expiry_date_object)
    # print(expiry_date_object_list)

    results = [d for d in sorted(expiry_date_object_list) if d > datetime.datetime.strptime(today, '%d-%m-%Y')]
    output = results[0] if results else None

    op = '%s%s%s' % (output.year, output.month, output.day)
    new_string = op[2:]
    #     print(new_string)
    return new_string


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    while (True):
        try:
            time.sleep(10)
            to_db_dict = {}
            # Check if it is trade time
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            to_db_dict["timestamp"] = now

            # symbol = "NIFTY"
            to_db_dict["symbol"] = "NIFTY"

            if is_it_trade_time():
                print("Its trade time")
                to_db_dict["is_trade_time"] = "Y"
                history = get_history("NSE:NIFTY50-INDEX")

                df = pd.DataFrame(history['candles'], columns=['epoch', 'open', 'high', 'low', 'close', 'volume'])
                nifty_stockstats_df = StockDataFrame(df)

                nifty_stockstats_df[['epoch', 'close_20_sma', 'close_7_smma', 'close_9_ema']]
                nifty_stockstats_df = nifty_stockstats_df.round()

                # Check if current price of selected index is greater than ema9
                current_price = nifty_stockstats_df['close'].iloc[-1]
                print("current_price -", current_price)
                current_ema9_price = nifty_stockstats_df['close_9_ema'].iloc[-1]
                print("current_ema9_price -", current_ema9_price)


                to_db_dict["current_price"] = str(current_price)
                to_db_dict["current_ema9_price"] = str(current_ema9_price)

                if (current_price > current_ema9_price):

                    # Decision to buy call
                    print("Current price > EMA9")
                    print("Taking call path")

                    to_db_dict["call_or_put"] = "call"

                    # Get option chain from NSE website and get strike prices between 120 and 150
                    # symbol = "NIFTY"

                    # to_db_dict["symbol"] = "NIFTY"

                    optionchain = get_option_chain_dataframe("NIFTY")
                    # print(optionchain.to_markdown())
                    call_strikeprice_df = optionchain[optionchain["CALL LTP"].ge(119) & optionchain["CALL LTP"].lt(151)][
                        "STRIKE PRICE"]
                    call_strikeprice_list = call_strikeprice_df.tolist()
                    # call_strikeprice_list.append(19600)
                    call_strikeprice = min(call_strikeprice_list)
                    print('Strike price -', call_strikeprice)

                    to_db_dict["strike_price"] = call_strikeprice

                    if not call_strikeprice_list:
                        # If no strike price available, abort
                        print("No call strike price available")
                    else:

                        expiry_options_call = get_next_expiry()
                        symbol_options_call = "NSE:NIFTY" + str(expiry_options_call) + str(call_strikeprice) + "CE"

                        history_options_call = get_history(symbol_options_call)
                        df_call = pd.DataFrame(history_options_call['candles'], columns=['epoch', 'open', 'high', 'low', 'close', 'volume'])
                        nifty_stockstats_df_options_call = StockDataFrame(df_call)
                        nifty_stockstats_df_options_call[['epoch', 'close_20_sma', 'close_7_smma', 'close_9_ema']]
                        nifty_stockstats_df_options_call = nifty_stockstats_df_options_call.round()

                        close_7_sma_list = nifty_stockstats_df_options_call['close_7_smma']
                        close_7_sma_list = close_7_sma_list.tolist()
                        close_20_smma_list = nifty_stockstats_df_options_call['close_20_sma']
                        close_20_smma_list = close_20_smma_list.tolist()
                        array1 = np.array(close_7_sma_list)
                        array2 = np.array(close_20_smma_list)

                        difference_array = np.subtract(array1, array2)
                        difference_list = list(difference_array)
                        nifty_stockstats_df_options_call = nifty_stockstats_df_options_call.assign(difference=difference_list)

                        smma_greater_than_sma_list = []

                        for value in nifty_stockstats_df_options_call.index:
                            n = nifty_stockstats_df_options_call['difference'][value]
                            if n >= 0:
                                if n == 0:
                                    smma_greater_than_sma_list.append("NA")
                                else:
                                    smma_greater_than_sma_list.append("Y")
                            else:
                                smma_greater_than_sma_list.append("N")
                        nifty_stockstats_df_options_call = nifty_stockstats_df_options_call.assign(smma_gt_sma=smma_greater_than_sma_list)

                        last_but_one_difference = nifty_stockstats_df_options_call['smma_gt_sma'].iloc[-2]
                        last_difference = nifty_stockstats_df_options_call['smma_gt_sma'].iloc[-1]

                        current_smma = nifty_stockstats_df_options_call['close_7_smma'].iloc[-1]
                        print("current_smma -", current_smma)
                        current_sma = nifty_stockstats_df_options_call['close_20_sma'].iloc[-1]
                        print("current_sma -", current_sma)

                        to_db_dict["close_20_sma"] = current_sma
                        to_db_dict["close_7_smma"] = current_smma

                        if (last_but_one_difference == 'Y') & (last_difference == 'Y'):
                            print("SMMA is greater than SMA")
                            to_db_dict["smma_greater_than_sma"] = "Y"

                            expiry = get_next_expiry()
                            symbol = "NSE:NIFTY" + str(expiry) + str(call_strikeprice) + "CE"
                            timestamp_list = find_hammer_candles(symbol, current_smma)

                            # timestamp_list = find_hammer_candles("^NSEI")

                            last_hammer_formed_time = timestamp_list[-1]
                            # now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            # to_db_dict["timestamp"] = now
                            time_difference = get_time_difference(now, last_hammer_formed_time)
                            if time_difference < 70:
                                to_db_dict["hammer_formed"] = "Y"
                                last_adx_value = get_adx_value()
                                to_db_dict["adx_value"] = last_adx_value
                                if (last_adx_value > 19.5):
                                    print("Buy now")
                                    to_db_dict["buy_signal"] = "Y"
                            else:
                                print("No hammer candle formed in last 5 mins")
                                to_db_dict["hammer_formed"] = "N"
                                # time.sleep(2)
                        else:
                            print("SMA is greater than SMMA")
                            to_db_dict["smma_greater_than_sma"] = "N"
                            # time.sleep(2)

                else:

                    # Decision to buy put
                    print("Current price < EMA9")
                    print("Taking put path")

                    to_db_dict["call_or_put"] = "put"

                    # Get option chain from NSE website and get strike prices between 120 and 150
                    # symbol = "NIFTY"

                    # to_db_dict["symbol"] = "NIFTY"

                    optionchain = get_option_chain_dataframe("NIFTY")
                    # print(optionchain.to_markdown())
                    put_strikeprice_df = optionchain[optionchain["PUT LTP"].ge(119) & optionchain["PUT LTP"].lt(151)][
                        "STRIKE PRICE"]
                    put_strikeprice_list = put_strikeprice_df.tolist()
                    put_strikeprice = min(put_strikeprice_list)

                    to_db_dict["strike_price"] = put_strikeprice

                    if not put_strikeprice_list:
                        print("No put strike price available")
                    else:

                        expiry_options_put = get_next_expiry()
                        symbol_options_put = "NSE:NIFTY" + str(expiry_options_put) + str(put_strikeprice) + "CE"

                        history_options_put = get_history(symbol_options_put)
                        df_put = pd.DataFrame(history_options_put['candles'], columns=['epoch', 'open', 'high', 'low', 'close', 'volume'])
                        nifty_stockstats_df_options_put = StockDataFrame(df_put)
                        nifty_stockstats_df_options_put[['epoch', 'close_20_sma', 'close_7_smma', 'close_9_ema']]
                        nifty_stockstats_df_options_put = nifty_stockstats_df_options_put.round()

                        close_7_sma_list = nifty_stockstats_df_options_put['close_7_smma']
                        close_7_sma_list = close_7_sma_list.tolist()
                        close_20_smma_list = nifty_stockstats_df_options_put['close_20_sma']
                        close_20_smma_list = close_20_smma_list.tolist()
                        array1 = np.array(close_7_sma_list)
                        array2 = np.array(close_20_smma_list)

                        difference_array = np.subtract(array1, array2)
                        difference_list = list(difference_array)
                        nifty_stockstats_df_options_put = nifty_stockstats_df_options_put.assign(difference=difference_list)

                        smma_greater_than_sma_list = []

                        for value in nifty_stockstats_df_options_put.index:
                            n = nifty_stockstats_df_options_put['difference'][value]
                            if n >= 0:
                                if n == 0:
                                    smma_greater_than_sma_list.append("NA")
                                else:
                                    smma_greater_than_sma_list.append("Y")
                            else:
                                smma_greater_than_sma_list.append("N")
                        nifty_stockstats_df_options_put = nifty_stockstats_df_options_put.assign(smma_gt_sma=smma_greater_than_sma_list)

                        last_but_one_difference = nifty_stockstats_df_options_put['smma_gt_sma'].iloc[-2]
                        last_difference = nifty_stockstats_df_options_put['smma_gt_sma'].iloc[-1]

                        current_smma = nifty_stockstats_df_options_put['close_7_smma'].iloc[-1]
                        print("current_smma -", current_smma)
                        current_sma = nifty_stockstats_df_options_put['close_20_sma'].iloc[-1]
                        print("current_sma -", current_sma)

                        to_db_dict["close_20_sma"] = current_sma
                        to_db_dict["close_7_smma"] = current_smma

                        if (last_but_one_difference == "Y") & (last_difference == "Y"):
                            print("SMMA is greater than SMA")
                            to_db_dict["smma_greater_than_sma"] = "Y"

                            expiry = get_next_expiry()
                            symbol = "NSE:NIFTY" + str(expiry) + str(put_strikeprice) + "PE"
                            timestamp_list = find_hammer_candles(symbol, current_smma)

                            # timestamp_list = find_hammer_candles("^NSEI")

                            last_hammer_formed_time = timestamp_list[-1]
                            # now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            # to_db_dict["timestamp"] = now
                            time_difference = get_time_difference(now, last_hammer_formed_time)
                            print(time_difference)
                            if time_difference < 70:
                                to_db_dict["hammer_formed"] = "Y"
                                last_adx_value = get_adx_value()
                                to_db_dict["adx_value"] = last_adx_value
                                if (last_adx_value > 19.5):
                                    print("Buy now")
                                    to_db_dict["buy_signal"] = "Y"
                            else:
                                print("No hammer candle formed in last 5 mins")
                                to_db_dict["hammer_formed"] = "N"
                                # time.sleep(2)
                        else:
                            print("SMA is greater than SMMA")
                            to_db_dict["smma_greater_than_sma"] = "N"
                            # time.sleep(2)
            else:
                print("not a trade time")
                to_db_dict["is_trade_time"] = "N"
                time.sleep(60)

            update_db(to_db_dict)
        except Exception as e:
            print(e)
            continue

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
