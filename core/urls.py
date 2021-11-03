from django.urls import path
from .views import (
    ItemDetailView,
    HomeView,
    ShopView,
    OrderSummaryView,
    CheckoutView,
    PaymentView,
    AddCouponView,
    RequestRefundView,
    CategoryView,
    add_to_wishlist,
    remove_from_wishlist,
    updateitem,
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('category/<slug>/', CategoryView.as_view(), name='category'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('add_coupon/', AddCouponView.as_view(), name='add-coupon'),
    path('shop/', ShopView.as_view(), name='shop'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('request-refund/', RequestRefundView.as_view(), name='request-refund'),
    path('add-to-wishlist/', add_to_wishlist, name='add-to-wishlist'),
    path('remove-from-wishlist/', remove_from_wishlist, name='remove-from-wishlist'),
    path('update_item/', updateitem, name="update_item"),
]
