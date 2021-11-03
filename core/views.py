from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, DetailView, View
from django.shortcuts import redirect
from django.utils import timezone
from .forms import CheckoutForm, CouponForm, RefundForm, PaymentForm
from .models import *
from .content_based import recommendation
from .collaboration_based import TopItemForUser
from django.http import HttpResponseRedirect
import json
from .utils import cookieCart, cartData, guestOrder
from django.core.serializers.json import DjangoJSONEncoder




# Create your views here.
import random
import string
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


def products(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "products.html", context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, status='D')
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = BillingAddress.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = BillingAddress.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})
            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:home")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, status='D')
            if form.is_valid():

                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print("Using the defualt shipping address")
                    address_qs = BillingAddress.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = BillingAddress(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")

                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = BillingAddress.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = BillingAddress(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")

                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")


class PaymentView(View):
    def get(self, *args, **kwargs):
        # order
        order = Order.objects.get(user=self.request.user, status='D')
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False,
                'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
            }
            userprofile = self.request.user.userprofile
            if userprofile.one_click_purchasing:
                # fetch the users card list
                cards = stripe.Customer.list_sources(
                    userprofile.stripe_customer_id,
                    limit=3,
                    object='card'
                )
                card_list = cards['data']
                if len(card_list) > 0:
                    # update the context with the default card
                    context.update({
                        'card': card_list[0]
                    })
            return render(self.request, "payment.html", context)
        else:
            messages.warning(
                self.request, "u have not added a billing address")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, status='D')

        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)
        if form.is_valid():
            token = form.cleaned_data.get('stripeToken')
            save = form.cleaned_data.get('save')
            use_default = form.cleaned_data.get('use_default')

            if save:
                if userprofile.stripe_customer_id != '' and userprofile.stripe_customer_id is not None:
                    customer = stripe.Customer.retrieve(
                        userprofile.stripe_customer_id)
                    customer.sources.create(source=token)

                else:
                    customer = stripe.Customer.create(
                        email=self.request.user.email,
                    )
                    customer.sources.create(source=token)
                    userprofile.stripe_customer_id = customer['id']
                    userprofile.one_click_purchasing = True
                    userprofile.save()

            amount = int(order.get_total() * 100)

            try:

                if use_default or save:
                    # charge the customer because we cannot charge the token more than once
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="usd",
                        customer=userprofile.stripe_customer_id
                    )
                else:
                    # charge once off on the token
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="usd",
                        source=token
                    )

                # create the payment
                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                # assign the payment to the order

                # order_items = OrderItem.objects.filter(order=order, status='P')
                # order_items.update(ordered=True)
                # for orderitem in order_items:
                #     orderitem.item.stock_no -= orderitem.quantity
                #     orderitem.item.save()
                #     orderitem.save()

                orderitem = OrderItem.objects.filter(order=order)
                for items in orderitem:
                    items.item.stock_no -= items.quantity
                    items.item.save()


                order.status = 'P'
                order.payment = payment
                order.ref_code = create_ref_code()
                order.save()

                messages.success(self.request, "Your order was successful!")
                return redirect("/")

            except stripe.error.CardError as e:
                body = e.json_body
                err = body.get('error', {})
                messages.warning(self.request, f"{err.get('message')}")
                return redirect("/")

            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.warning(self.request, "Rate limit error")
                return redirect("/")

            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                print(e)
                messages.warning(self.request, "Invalid parameters")
                return redirect("/")

            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.warning(self.request, "Not authenticated")
                return redirect("/")

            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.warning(self.request, "Network error")
                return redirect("/")

            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.warning(
                    self.request, "Something went wrong. You were not charged. Please try again.")
                return redirect("/")

            except Exception as e:
                # send an email to ourselves
                print(e)
                messages.warning(
                    self.request, "A serious error occurred. We have been notifed.")
                return redirect("/")

        messages.warning(self.request, "Invalid data received")
        return redirect("/payment/stripe/")


class HomeView(ListView):
    template_name = "index.html"
    context_object_name = 'items'
    def get_queryset(self):
        item = Item.objects.raw('''select * from core_item left outer join core_wishlist 
                                    on core_item.id = core_wishlist.wished_item_id 
                                    and core_wishlist.user_id = %s 
                                    where core_item.is_active is not null''', [self.request.user.id])
        return item
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        if self.request.user.is_authenticated:
            context['related'] = TopItemForUser(self.request.user.id, 10)
        return context




# class OrderSummaryView(LoginRequiredMixin, View):
#     def get(self, *args, **kwargs):
#         try:
#             order = Order.objects.get(user=self.request.user, ordered=False)
#             context = {
#                 'object': order
#             }
#             return render(self.request, 'order_summary.html', context)
#         except ObjectDoesNotExist:
#             messages.error(self.request, "You do not have an active order")
#             return redirect("/")

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            data = cartData(self.request)
            cartItems = data['cartItems']
            order = data['order']
            items = data['items']
            context = {'items': items, 'order': order, 'cartItems': cartItems}
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order")
            return redirect("/")

class ShopView(ListView):
    model = Item
    paginate_by = 6
    template_name = "shop.html"

    def get_context_data(self, **kwargs):
        data = cartData(self.request)

        cartItems = data['cartItems']
        order = data['order']
        items = data['items']
        products = Item.objects.raw('''select * from core_item left outer join core_wishlist 
                                       on core_item.id = core_wishlist.wished_item_id 
                                       and core_wishlist.user_id = %s 
                                       where core_item.is_active is not null''', [self.request.user.id])
        context = {'products': products, 'cartItems': cartItems}
        return context


class ItemDetailView(DetailView):
    model = Item
    models_name = Recommendation.objects.values('models_name')[0]
    template_name = "product-detail.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all
        context['related'] = recommendation(context['object'].title, 8, self.models_name['models_name'] )
        return context

# class CategoryView(DetailView):
#     model = Category
#     template_name = "category.html"

from itertools import chain


class CategoryView(View):
    def get(self, *args, **kwargs):
        category = Category.objects.get(slug=self.kwargs['slug'])
        # item = Item.objects.filter(category=category, is_active=True)
        item = Item.objects.raw('''select * from core_item left outer join core_wishlist 
                                       on core_item.id = core_wishlist.wished_item_id 
                                       and core_wishlist.user_id = %s 
                                       where core_item.is_active is not null
                                        and core_item.category_id = %s ''', [self.request.user.id, category.id])
        context = {
            'object_list': item,
            'category_title': category,
            'category_description': category.description,
            'category_image': category.image
        }
        return render(self.request, "category.html", context)





# def home(request):
#     context = {
#         'items': Item.objects.all()
#     }
#     return render(request, "index.html", context)
#
#
# def products(request):
#     context = {
#         'items': Item.objects.all()
#     }
#     return render(request, "product-detail.html", context)
#
#
# def shop(request):
#     context = {
#         'items': Item.objects.all()
#     }
#     return render(request, "shop.html", context)


# @login_required
# def add_to_cart(request, slug):
#     item = get_object_or_404(Item, slug=slug)
#     order_qs , created= Order.objects.get_or_create(user=request.user, ordered=False, ordered_date = timezone.now())
#     order_item, created = OrderItem.objects.get_or_create(
#         item=item,
#         user=request.user,
#         order=order_qs,
#         ordered=False
#     )
#     order = order_qs
#     # check if the order item is in the order
#     if order.items.filter(item__slug=item.slug).exists():
#         order_item.quantity += 1
#         order_item.save()
#         messages.info(request, "This item quantity was updated.")
#         return redirect("core:order-summary")
#     else:
#         order.items.add(order_item)
#         messages.info(request, "This item was added to your cart.")
#         return redirect("core:order-summary")
#
#
#
# @login_required
# def remove_from_cart(request, slug):
#     item = get_object_or_404(Item, slug=slug)
#     order_qs = Order.objects.filter(
#         user=request.user,
#         ordered=False)
#     if order_qs.exists():
#         order = order_qs[0]
#         # check if the order item is in the order
#         if order.items.filter(item__slug=item.slug).exists():
#             order_item = OrderItem.objects.filter(
#                 item=item,
#                 user=request.user,
#                 ordered=False
#             )[0]
#             order.items.remove(order_item)
#             messages.info(request, "Item was removed from your cart.")
#             return redirect("core:order-summary")
#         else:
#             # add a message saying the user dosent have an order
#             messages.info(request, "Item was not in your cart.")
#             return redirect("core:product", slug=slug)
#     else:
#         # add a message saying the user dosent have an order
#         messages.info(request, "u don't have an active order.")
#         return redirect("core:product", slug=slug)
#     return redirect("core:product", slug=slug)
#
#
# @login_required
# def remove_single_item_from_cart(request, slug):
#     item = get_object_or_404(Item, slug=slug)
#     order_qs = Order.objects.filter(
#         user=request.user,
#         ordered=False)
#     if order_qs.exists():
#         order = order_qs[0]
#         # check if the order item is in the order
#         if order.items.filter(item__slug=item.slug).exists():
#             order_item = OrderItem.objects.filter(
#                 item=item,
#                 user=request.user,
#                 ordered=False
#             )[0]
#             if order_item.quantity > 1:
#                 order_item.quantity -= 1
#                 order_item.save()
#             else:
#                 order.items.remove(order_item)
#             messages.info(request, "This item qty was updated.")
#             return redirect("core:order-summary")
#         else:
#             # add a message saying the user dosent have an order
#             messages.info(request, "Item was not in your cart.")
#             return redirect("core:product", slug=slug)
#     else:
#         # add a message saying the user dosent have an order
#         messages.info(request, "u don't have an active order.")
#         return redirect("core:product", slug=slug)
#     return redirect("core:product", slug=slug)


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, status='D')
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("core:checkout")


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            # edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request was received")
                return redirect("core:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist")
                return redirect("core:request-refund")




@login_required
def add_to_wishlist(request):
    if request.method == 'GET':
        item_id = request.GET['item_id']
        likeditem = Item.objects.get(id=item_id)
        if not Wishlist.objects.filter(wished_item=likeditem, user=request.user):
            m = Wishlist(wished_item=likeditem, user=request.user)
            m.save()
            messages.info(request, 'The item was added to your wishlist')
            return HttpResponse('success')
        else:
            return HttpResponse("unsuccesful")
    else:
        messages.info(request, 'The item was failed to add to your wishlist')
        return HttpResponse("unsuccesful")


@login_required
def remove_from_wishlist(request):
    if request.method == 'GET':
        item_id = request.GET['item_id']
        likeditem = Item.objects.get(id=item_id)
        Wishlist.objects.filter(wished_item=likeditem, user=request.user).delete()

        messages.info(request, 'The item was delete from your wishlist')
        return HttpResponse('success')
    else:
        messages.info(request, 'The item was failed to del from your wishlist')
        return HttpResponse("unsuccesful")






def updateitem(request):
    data = json.loads(request.body)
    itemid = data['itemId']
    action = data['action']
    numProductOrder = data['numProductOrder']
    print('Action:', action)
    print('Item:', itemid)
    print('numProductOrder', numProductOrder)
    customer = request.user
    product = Item.objects.get(id=itemid)
    # order, created = Order.objects.get_or_create(user=customer, ordered=False, ordered_date=timezone.now())
    orders = Order.objects.filter(user=customer, status='D')
    order = orders.first() if orders.exists() else Order.objects.create(user=customer, ordered_date=timezone.now())
    orderItem, created = OrderItem.objects.get_or_create(order=order, item=product, user_id=customer.id)
    if action == 'add':
        orderItem.quantity = (orderItem.quantity + int(numProductOrder))
        if orderItem.quantity > int(product.stock_no):
            orderItem.quantity = int(product.stock_no)
            messages.info(request, "cant order more than products in stock")
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)
    orderItem.save()
    if orderItem.quantity <= 0 or action == 'removeall':
        orderItem.delete()

    # assuming obj is a model instance
    rep_cart = OrderItem.objects.filter(user=customer, order=order)\
        .values('item_id', 'item_id__title', 'quantity', 'item_id__price', 'item_id__discount_price', 'item_id__image','item_id__large_image_url', 'order_id__coupon_id__amount')
    data = json.dumps(list(rep_cart), cls=DjangoJSONEncoder)
    return JsonResponse(data, safe=False)



