
import numpy as np
import pandas as pd
import json
import yfinance as yf
import queue
import threading
import os
from .blackAlt_list import black_list, alt_list

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


# scrape from wiki to get the ticker list and the ticker-name
# preferably only want to run once manually


def genJson_sp500() -> None:

    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'

    print("scraping from wiki to get the ticker list")

    # return list of dataframe
    list_of_df_sp500 = pd.read_html(url)
    table_df = list_of_df_sp500[0]

    # select this 2 column
    res_df = table_df[['Symbol', 'Security']]
    res_df.rename(columns={'Security': 'ticker'}, inplace=True)

    # add another columm, to handle when ticker symbol does not tally with one scraped from wiki
    res_df = res_df.assign(Alt_Symbol=None)

    # convert into dict
    dic1 = res_df.set_index('Symbol').to_dict('index')

    scriptPath = os.path.dirname(os.path.realpath(__file__))
    fp = os.path.join(scriptPath, 'sp500_info.json')
    # print(fp)

    # save as json  file
    with open(fp, 'w') as fi:
        json.dump(dic1, fi)
        print("json file saved !!! ")


# main method to get the latest stock price interfacing with yfinance
def processYf_stockPrice(processBool=False) -> dict | None:

    print("calling processYf_stockPrice v2 now !!!")

    # collect the results in the queue from threds
    que = queue.Queue()

    # should not want to trigger after we had the json file
    if processBool:
        genJson_sp500()

    print("begin to mass fetch the data ...")

    scriptPath = os.path.dirname(os.path.realpath(__file__))
    fp = os.path.join(scriptPath, 'sp500_info.json')

    # load tickers as dict from json file
    with open(fp) as f:
        tickerDic = json.load(f)

    # the ticker symbol are the keys
    symbol_lis = list(tickerDic.keys())

    # apply filtering using alt list and black list
    blackList: list = black_list
    altList: list = alt_list

    # do some filtering so that only valid symbol will be use for fetching
    # get those not in blacklist
    # use the alt symbol to fetch data since the  symbol from wiki dont work
    finalLis = [x if x not in altList else tickerDic[x]['Alt_Symbol']
                for x in symbol_lis if x not in blackList]

    # mass fetch the data using the list of symbol for close
    # get df of 2 day information
    res_df = getTickerOpenClosedPrice(finalLis)

    print("mass fetch data completed !!!")

    # prev closing price
    prevClosedPrice_df: pd.DataFrame = res_df.iloc[0]['Close']

    # closing price
    closedPrice_df: pd.DataFrame = res_df.iloc[1]['Close']

    # open price
    openPrice_df: pd.DataFrame = res_df.iloc[1]['Open']

    # rename the column of for each df
    openPrice_df.rename("Open", inplace=True)
    prevClosedPrice_df.rename("prev_Close", inplace=True)
    closedPrice_df.rename("Close", inplace=True)

    # merge them to form the dataframe based on index
    temp1 = pd.concat([openPrice_df, prevClosedPrice_df], axis=1)
    temp = pd.concat([temp1, closedPrice_df], axis=1)

    print("1st stage of dataframe merge done !!!")

    # =============update df to fill up the nan value=============

    # check nan values, collect data from alt symbol and add to queue
    checkTickerData(temp, que)

    # que not empty means update is required for some tickers
    if not que.empty():

        print("updating nan values ...")

        errorData = list(que.queue)

        # update value of the df
        # list of dict
        # in each dict, symbol is the key -k
        # and value is another dict with the updated value -v
        for x in errorData:
            (k, v), = x.items()

            print(k, v)

            if v['prevCls']:
                temp.loc[k]['prev_Close'] = v['prevCls']

            if v['clsPrice']:
                temp.loc[k]['Close'] = v['clsPrice']

            if v['openPrice']:
                temp.loc[k]['Open'] = v['openPrice']

    # rename those symbol index that use the alt symbol
    # to rename pass in dict of oldName: newName

    if alt_list:
        renameDict = {tickerDic[x]['Alt_Symbol']: x for x in alt_list}
        temp = (temp.rename(index=renameDict))

    # =============combine the 2 dataframe into 1  before converting to dict=============

    print("final stage- combining dataframe ...")

    # transform tickerDict into dataframe
    df1 = pd.DataFrame.from_dict(tickerDic, orient='index')

    # get the time portion from index
    ts = res_df.index[1]
    tz = ts.tz_localize(tz='America/New_York')

    # add the time col to the dataframe
    # df2 = df2.assign(dateTime=timeCol_value)

    # join based on index, which is the ticker symbol
    latestPrice_df = df1.join(temp)
    latestPrice_dict = latestPrice_df.to_dict('index')

    print("latest close price data ready !!!")

    result_dict = {'data': latestPrice_dict, 'timeDate': tz}

    return result_dict


# call download method to mass get data
# the download method does not throw if it cant get data from a symbol, it just insert nan
def getTickerOpenClosedPrice(symbol_lis: list) -> pd.DataFrame:

    data_df = yf.download(

        symbol_lis,
        # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        period="2d",
    )

    # get the latest close open price
    return data_df


# check if  any  colum contain nan,
# nan will indicate data for the symbol was not retrieved from the 1st method
# will need to manually verify if the ticker symbol matches , if data exist for the symbol in the yahoo website
# in the case of ticker mismatch, manually update the alt symbol in the json file


def checkTickerData(df: pd.DataFrame, que: queue) -> list:

    print("detecting symbol with missing data ...")

    # get list of ticker where the symbol cannot get data intially for any columns
    errIndex = np.where(df.isna().any(axis=1))[0]
    errorList = [df.iloc[x].name for x in errIndex]

    if errorList:
        # using multi threading to fetch the data using alt symbol
        getYf_data_thread(errorList, que)

    else:
        print("no symbol with missing data detected")

    return errorList


def get_TickerOpenClosePrevClosePrice(q, symbol):

    # try again using the symbol, data maynot be ready that time
    try:
        ticker = yf.Ticker(symbol)
        twoDay_df = ticker.history(period="2d")

        # prev price
        prevCls_price = twoDay_df.iloc[0]['Close']

        # latest cls price
        clsPrice = twoDay_df.iloc[1]['Close']

        # latest open price
        openPrice = twoDay_df.iloc[1]['Open']

        # put inside queue
        q.put({symbol: {'prevCls': prevCls_price,
              'clsPrice': clsPrice, 'openPrice': openPrice}})

    except Exception as e:
        print(e)


# spawn thread to fetch each ticker data that encounter error
def getYf_data_thread(errorList: list, que: queue):

    print("using threads to fetch data ...")

    threadList = []
    for x in errorList:
        t = threading.Thread(target=get_TickerOpenClosePrevClosePrice, args=(
            que, x))
        threadList.append(t)

    for x in threadList:
        x.start()

    for x in threadList:
        x.join()


if __name__ == "__main__":
    # genJson_sp500()
    processYf_stockPrice()
    pass
