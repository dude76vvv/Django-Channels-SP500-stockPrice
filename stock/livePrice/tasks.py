import time
from celery import shared_task
from channels.layers import get_channel_layer
from .models import Ticker
from .helper import sp500
from django.forms.models import model_to_dict
from asgiref.sync import async_to_sync
import pandas as pd
import math
from datetime import datetime
import pytz
from threading import Thread
import threading
from .serializer import TickerSerializer


from queue import Queue

# for saving result from thread
queResult = Queue()

# for adding the items to be process
queProcess = Queue()

# should yield a better performance if database allow multi threading write/save


def consumer(_queProcess: Queue, _queResult: Queue, tickerDict: dict, _time: datetime):
    print('Consumer: Running')

    while True:

        try:
            symbolItem = _queProcess.get(timeout=1)

        except Exception as e:
            print(f"time out-{threading.get_ident()}")
            break

        print(f"working on {symbolItem} - {threading.get_ident()}")

        # do the processing here
        try:
            obj, created = Ticker.objects.get_or_create(symbol=symbolItem)
            obj.name = tickerDict[symbolItem]['ticker']

            if not math.isnan(tickerDict[symbolItem]['Close']):
                obj.closePrice = tickerDict[symbolItem]['Close']

            if not math.isnan(tickerDict[symbolItem]['Open']):
                obj.openPrice = tickerDict[symbolItem]['Open']

            if not math.isnan(tickerDict[symbolItem]['prev_Close']):
                obj.prevClosePrice = tickerDict[symbolItem]['prev_Close']

            if not math.isnan(tickerDict[symbolItem]['prev_Close']) and not math.isnan(tickerDict[symbolItem]['Close']):
                diff = tickerDict[symbolItem]['Close'] - \
                    tickerDict[symbolItem]['prev_Close']

                obj.state = 'rise' if diff > 0 else 'fall'
                obj.change = diff

            obj.save()

            # only serialize these fields for the object
            someFields = ['symbol', 'name', 'closePrice',
                          'openPrice', 'prevClosePrice', 'state', 'change']

            objDict = model_to_dict(obj, fields=someFields)

            # objDict = TickerSerializer(obj, many=False).data
            # print(objDict)

            queResult.put(objDict)
            print(f"{symbolItem} processed by consumer")

        except Exception as e:
            print(e)
            time.sleep(5)

    # queProcess.task_done()
    print(f"Consumer: Done- {threading.get_ident()}")
    print(f"queProcess size- {queProcess.qsize()}")
    print(f"queResult size- {queResult.qsize()}")
    return


channel_layer = get_channel_layer()


@shared_task
def get_yf_data_task():

    print("task triggered")

    fetchedRes: dict = sp500.processYf_stockPrice()

    # to contain the model object
    dataLis = []

    # saved the ticker information into model object
    tickers: dict = fetchedRes['data']
    # timeDate_pd: pd.Timestamp = fetchedRes['timeDate']
    # timeDate = timeDate_pd.to_pydatetime()

    print("working on saving data to database ...")

    # work with time aware utc for ez converting to any timezone
    processTime = datetime.now(pytz.utc)
    processTimeEst = processTime.astimezone(pytz.timezone('US/Eastern'))
    processTimeEstStr = processTime.astimezone(pytz.timezone(
        'US/Eastern')).strftime('%Y-%m-%d %H:%M:%S %Z%z')

    # to calculate process time

    # -----------synchronous db save/write-----------
    startTime = datetime.now()

    for k, v in tickers.items():
        print(f"processing symbol: {k} ")
        # print(v)

        try:
            obj, created = Ticker.objects.get_or_create(symbol=k)
            obj.name = v['ticker']

            if not math.isnan(v['Close']):
                obj.closePrice = v['Close']

            if not math.isnan(v['Open']):
                obj.openPrice = v['Open']

            if not math.isnan(v['prev_Close']):
                obj.prevClosePrice = v['prev_Close']

            if not math.isnan(v['prev_Close']) and not math.isnan(v['Close']):
                diff = v['Close'] - v['prev_Close']

                obj.state = 'rise' if diff > 0 else 'fall'
                obj.change = diff

            obj.timeStamp = processTimeEst
            obj.save()

            # only serialize these fields with the object
            someFields = ['symbol', 'name', 'closePrice',
                          'openPrice', 'prevClosePrice', 'state', 'change']

            objDict = model_to_dict(obj, fields=someFields)

            # objDict = TickerSerializer(obj, many=False).data
            # print(objDict)

            dataLis.append(objDict)

        except Exception as e:
            print(e)

    # -----------using thread to save at db start-----------

    # put the keys into the que
    # for x in tickers.keys():
    #     queProcess.put(x)

    # print(f"{queProcess.qsize()}")

    # # queProcess.put(None)

    # startTime = datetime.now()
    # # 5consumer thread to finish the queue asap
    # totalThreads = 5
    # threadList = []
    # for i in range(totalThreads):
    #     ct = Thread(target=consumer, args=(
    #         queProcess, queResult, tickers, timeDate))
    #     threadList.append(ct)
    #     ct.start()

    # for x in threadList:
    #     x.join()

    # # convert queue result to list
    # dataLis = list(queResult.queue)

    # -----------using thread to save at db end-----------

    # final data to send out
    latestPrice = {"data": dataLis, 'timeDate': processTimeEstStr}

    print('task done')

    print(f"time taken: {datetime.now()-startTime}")

    async_to_sync(channel_layer.group_send)(
        # group_name
        "livePrice",
        {
            # handle method in the group
            "type": "sendData",
            "data": latestPrice
        }
    )


# starting worker command can trigger the function
# get_yf_data_task()
