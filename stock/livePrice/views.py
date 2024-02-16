import time
from django.shortcuts import render
from .models import Ticker
from .tasks import get_yf_data_task
from django.views import View
from django.http import JsonResponse
from datetime import datetime
import pytz

# Create your views here.


def welcome_page_view(request):
    return render(request, "welcome.html")


def test(request):
    return render(request, "test.html")


# websocket will be inserted within this html page to receive live data constantly
# to render with existing data while waitng for the latest data
# def price_table_view(request):

#     # list of Ticker object pass down
#     allTickers = Ticker.objects.all()
#     dt = allTickers[0].timeStamp

#     # convert utc to new york time
#     dt_est = dt.astimezone(pytz.timezone('US/Eastern')
#                            ).strftime('%Y-%m-%d %H:%M:%S %Z%z')

#     context = {'allTickers': allTickers, 'datetime': dt_est}

#     return render(request, "livePrice/priceTable.html", context)


class StockTableView(View):

    def get(self, request):

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            print("received from client")
            print("client requesting update of data")

            # send to celery for processing
            task = get_yf_data_task.delay()
            print(task.task_id)

            return JsonResponse({'reply': 'updating table now. pls wait', 'statusAck': 200})

        allTickers = Ticker.objects.all()
        dt = allTickers[0].timeStamp

        # convert utc to new york time
        dt_est = dt.astimezone(pytz.timezone(
            'US/Eastern')).strftime('%Y-%m-%d %H:%M:%S %Z%z')

        context = {'allTickers': allTickers, 'datetime': dt_est}

        return render(request, "livePrice/priceTable.html", context)

    def post(self, request):
        pass
