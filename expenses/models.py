import datetime

from django.db import models
from django.urls.base import reverse


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f'{self.name}'


class Expense(models.Model):
    class Meta:
        ordering = ('-date', '-pk')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='expenses')
    name = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    date = models.DateField(default=datetime.date.today, db_index=True)

    def __str__(self):
        return f'{self.date} {self.name} {self.amount}'
