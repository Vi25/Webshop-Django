from django import template
from django.db.models import Exists
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from ..models import Order, OrderItem, Item

register = template.Library()


@register.filter
def cart_item_count(user):
    if user.is_authenticated:
        try:
            di = Order.objects.get(user=user, status='D')
            if di:
                qs = OrderItem.objects.filter(user=user, order=di)
                if qs.exists():
                    return qs.count()

        except ObjectDoesNotExist:
            return 0
    return 0


@register.simple_tag
def cart_item(user):
    try:
        if user.is_authenticated:
            di = Order.objects.get(user=user, status='D')
            if di:
                ci = OrderItem.objects.filter(order=di.id)
                return {'ci': ci, 'di': di}

    except ObjectDoesNotExist:
        return{'ci': ''}
