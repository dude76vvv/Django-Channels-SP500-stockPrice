import pandas as pd
import json
import yfinance as yf
import queue
import threading
import os


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

    # collect the results in the queue from threds
    que = queue.Queue()

    # should not want to trigger after we had the json file
    if processBool:
        genJson_sp500()

    print("begin to mass fetch the data ...")

    scriptPath = os.path.dirname(os.path.realpath(__file__))
    fp = os.path.join(scriptPath, 'sp500_info.json')

    # load ticker-list from json file
    with open(fp) as f:
        tickerDic = json.load(f)

    # the ticker symbol are the keys
    symbol_lis = list(tickerDic.keys())

    # mass fetch the data using the list of symbol
    init_df = getTickerPrice_1(symbol_lis)

    print("mass fetch data completed !!!")
    # =============update df to fill up the nan value=============

    # check nan values, collect data from alt symbol and add to queue
    checkTickerData(init_df, tickerDic, que)

    if not que.empty():

        print("updating nan values ...")

        errorData = list(que.queue)

        # update value of the df
        for x in errorData:
            (k, v), = x.items()
            if v:
                init_df[k] = v

    # =============combine the 2 dataframe into 1  before converting to dict=============

    print("final stage- combining dataframe ...")

    # transform tickerDict into dataframe
    df1 = pd.DataFrame.from_dict(tickerDic, orient='index')

    # get the time portion from index
    timeCol_value = init_df.index[0]

    # transpose to switch the rows and columns
    # this result in symbol to be the index
    init_df.reset_index(drop=True, inplace=True)
    df2 = init_df.T

    df2.rename(columns={0: "price"}, inplace=True)

    # add the time col to the dataframe
    # df2 = df2.assign(dateTime=timeCol_value)

    # join based on index, which is the ticker symbol
    latestPrice_df = df1.join(df2)
    latestPrice_dict = latestPrice_df.to_dict('index')

    print("latest close price data ready !!!")
    # print(latestPrice_dict)

    # for k, v in latestPrice_dict.items():
    #     print(v)
    #     print(v['ticker'])

    closedPrice_dict = {'data': latestPrice_dict, 'timedate': timeCol_value}

    return closedPrice_dict


# call download method to mass get data
# the download method does not throw if it cant get data from a symbol, it just insert nan
def getTickerPrice_1(symbol_lis: list) -> pd.DataFrame:

    data_df = yf.download(

        symbol_lis,
        # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        period="1d",

        # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        # (optional, default is '1d')
        interval="1m",

        # group_by = 'ticker',

        # adjust all OHLC automatically
        # (optional, default is False)
        auto_adjust=True,
    )

    # get the latest close price which is the last row
    data_df = data_df['Close'].tail(1)

    return data_df


# check if  any  colum contain nan,
# nan will indicate data for the symbol was not retrieved from the 1st method
# will need to manually verify if the ticker symbol matches , if data exist for the symbol in the yahoo website
# in the case of ticker mismatch, manually update the alt symbol in the json file

# the below function will attempt to get data from the alt symbol
def checkTickerData(df: pd.DataFrame, tickerDic: dict, que: queue) -> list:

    print("detecting symbol with missing data ...")

    # get list of ticker where the symbol cannot get data intially
    errorList = list(df.loc[:, df.isna().any()].columns)

    if errorList:
        # using multi threading to fetch the data using alt symbol
        getYf_data_thread(errorList, tickerDic, que)

    else:
        print("no symbol with missing data detected")

    return errorList


# getting each ticker data using yfinace history method
# use queue to collect data from thread
def getTickerPrice_altSymbol(q: queue, symbol: str, alt: str) -> None:

    print(f"thread working on symbol: {symbol} using alt symbol: {alt} ")

    if alt:

        try:

            ticker = yf.Ticker(alt)
            price = ticker.history(period="1d")['Close'].item()

            if price:
                q.put({symbol: price})
                print(f"data from symbol: {symbol} added to queue")

        except Exception as e:
            # raise e
            print(e)


# spawn thread to fetch each ticker data that encounter error
def getYf_data_thread(errorList: list, tickerDic: dict, que: queue):

    print("using threads to fetch data ...")

    threadList = []
    for x in errorList:
        t = threading.Thread(target=getTickerPrice_altSymbol, args=(
            que, x, tickerDic[x]['Alt_Symbol']))
        threadList.append(t)

    for x in threadList:
        x.start()

    for x in threadList:
        x.join()


if __name__ == "__main__":
    # genJson_sp500()
    processYf_stockPrice()
    pass
