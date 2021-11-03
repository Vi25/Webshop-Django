from django import template
from core.models import Order, OrderItem, Item


register = template.Library()

