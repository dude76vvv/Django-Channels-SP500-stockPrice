
from django.urls import path
from . import views


urlpatterns = [
    path("test", views.test, name="test"),  # example url stock/test
    # path("", views.price_table_view, name="stock_table"),
    # path("", views.price_table_view, name="stock_table"),
    path("", views.StockTableView.as_view(), name="stock_table"),

]
