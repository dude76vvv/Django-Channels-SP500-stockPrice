# Django-S&P500-stockPrice
The aim of this project is to use Django framework to develop a real-time stock price webpage.<br/>
Stock information such as open-price and close-price are available for viewing in table form. <br/>
Functionalities include table sorting, on-demand update and periodic update. 

3rd party module **yfinance** is the primary means to retrieve the latest price of the S&P tickers.<br/>
To allow webpage to remain responsive, resource-heavy and time-consuming process are offload to **Celery** to handle.<br/> 
To allow bi-directional communication between client and server, websocket is implemented in form of **Channels (ASGI)** 


## Features
* Real time stock price update for S&P 500
* Sorting of table 
* Mobile responsive
  
## Technologies used
* Django 
* yfinance
* Pandas
* Beautiful Soup
* Celery
* Redis
* Tailwind CSS
  

## Setting up

1. **CD** to the project folder and create virtual environment.
    - **python -m venv venv**

2. Activate virtual environment
    - **venv\Scripts\activate**

3. Install the required modules needed for application to run:
    - **pip install -r requirements.txt**
  
4. Install Redis in machine


## Running
1. start redis.
    - **redis-server**
  
![image](https://github.com/dude76vvv/Django-Channels-SP500-stockPrice/assets/131178280/6d248414-5f6b-4242-bdf1-253ad768223d)
  
2. **CD** to the stock folder and run command to start django server.
    - **python manage.py runserver**
  
  ![image](https://github.com/dude76vvv/Django-Channels-SP500-stockPrice/assets/131178280/a02219e1-83d3-47a5-947d-6a5e43d0cdd9)

  
3. Open another terminal/shell. **CD** to the stock folder and run command to start Celery.
    - **celery -A  stock worker -P solo -l info y**
  
![image](https://github.com/dude76vvv/Django-Channels-SP500-stockPrice/assets/131178280/562dd4ef-81f3-4b97-b25b-2e0e6c8f7d54)

### Periodic update (optional) 

1. Open another terminal/shell. **CD** to the stock folder and run command to start Celery beat.(_Celery must also be started_)
    - **celery -A stock beat -l INFO**
  
2. Configure the Celery beat schedule as desire.

![image](https://github.com/dude76vvv/Django-Channels-SP500-stockPrice/assets/131178280/698201eb-a30b-469a-818d-160c8e070d73)


## Screenshots
![image](https://github.com/dude76vvv/Django-Channels-SP500-stockPrice/assets/131178280/b463f2d4-aab2-4293-848b-b7742d0c6e1d)

![image](https://github.com/dude76vvv/Django-Channels-SP500-stockPrice/assets/131178280/d9cb2e55-1186-4e98-aa74-c6e407b5fe30)

![image](https://github.com/dude76vvv/Django-Channels-SP500-stockPrice/assets/131178280/f61090aa-471b-4f0e-9e34-35f7cd83c4b8)

![image](https://github.com/dude76vvv/Django-Channels-SP500-stockPrice/assets/131178280/87bad019-d7c8-4d9a-a131-62fc0a74bcfa)

![image](https://github.com/dude76vvv/Django-Channels-SP500-stockPrice/assets/131178280/88e93f8d-3237-4514-b22f-2bb32da9b6f0)

![image](https://github.com/dude76vvv/Django-Channels-SP500-stockPrice/assets/131178280/3c787f46-48a1-4709-933e-a847eb340cac)













