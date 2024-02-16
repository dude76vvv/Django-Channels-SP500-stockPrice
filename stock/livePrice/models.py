from django.db import models
from datetime import datetime

# Create your models here.


class Ticker(models.Model):

    symbol = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=50)
    closePrice = models.FloatField(default=0, blank=True)
    openPrice = models.FloatField(default=0, blank=True)
    prevClosePrice = models.FloatField(default=0, blank=True)

    # difference between close and prev close
    change = models.FloatField(default=0, blank=True)

    # indicate  a rise or fall
    state = models.CharField(max_length=10, default='stay')
    timeStamp = models.DateTimeField(default=datetime.now, blank=True)

    # openPrice = models.FloatField(default=0,blank=True)
    # prevPrice = models.FloatField(default=0,blank=True)
    # createdAt = models.DateTimeField(auto_now_add=True)

    # for arranging in the order and indexing
    class Meta:
        ordering = ['symbol', 'name']

        indexes = [
            models.Index(fields=['symbol', 'name'])
        ]

    # what to return when print object
    def __str__(self):
        return f"{self.symbol} | {self.name}"
