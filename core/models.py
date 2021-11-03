from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.shortcuts import reverse
from django_countries.fields import CountryField
from django.contrib.auth.models import User, AbstractUser
from django.utils import timezone




# Create your models here.
CATEGORY_CHOICES = (
    ('SB', 'Shirts And Blouses'),
    ('TS', 'T-Shirts'),
    ('SK', 'Skirts'),
    ('HS', 'Hoodies&Sweatshirts')
)

LABEL_CHOICES = (
    ('S', 'sale'),
    ('N', 'new'),
    ('P', 'promotion')
)

ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)
STATUS_CHOICES = (
    ('D', 'Draft'),
    ('U', 'Unpaid'),
    ('P', 'Paid'),
    ('S', 'Shiping'),
    ('F', 'Finished'),
    ('C', 'Canceled'),
)

MODELS_CHOICES = (
    ('BoW', 'Bag of Words'),
    ('tf-idf', 'TF-IDF'),
    ('idf', 'IDF'),
)

#extendingmodels
class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(default='accounting.png')
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    one_click_purchasing = models.BooleanField(default=False)
    name_order = models.CharField(max_length=200, null=True, default='guest')
    email_order = models.CharField(max_length=200)
    birthday = models.DateField(blank=True, null=True)
    phone_number = models.DecimalField(null=True, blank=True, decimal_places=0, max_digits=15)
    def __str__(self):
        return f"{ self.name_order } of ( {self.user} )"

class Recommendation(models.Model):
    models_name = models.CharField(choices=MODELS_CHOICES, max_length=10, default='tf-idf')
    # created = models.DateTimeField(editable=False)
    modified = models.DateTimeField(auto_now_add=False, auto_now=True, blank=True)
    title = models.CharField(max_length=50, null=True)
    # def save(self, *args, **kwargs):
    #     ''' On save, update timestamps '''
    #     if not self.id:
    #         self.created = timezone.now()
    #     self.modified = timezone.now()
    #     return super(User, self).save(*args, **kwargs)



#originalmodels


class Slide(models.Model):
    caption1 = models.CharField(max_length=100)
    caption2 = models.CharField(max_length=100)
    link = models.CharField(max_length=100)
    image = models.ImageField(help_text="Size: 1920x570")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "{} - {}".format(self.caption1, self.caption2)

class Category(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField()
    description = models.TextField(null=True)
    image = models.ImageField(help_text="Size: 500x500", null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:category", kwargs={
            'slug': self.slug
        })

class Brand(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(null=True)
    image = models.ImageField(null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Color(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(null=True)
    image = models.ImageField(null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Item(models.Model):
    title = models.CharField(max_length=200)
    price = models.FloatField()
    discount_price = models.FloatField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.DO_NOTHING)
    color = models.ForeignKey(Color, on_delete=models.DO_NOTHING)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1, default='N')
    slug = models.SlugField(max_length=200)
    stock_no = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    description_short = models.CharField(blank=True, max_length=50, null=True)
    description_long = models.TextField(blank=True, null=True)
    image = models.ImageField(blank=True, null=True)
    small_image_url = models.CharField(blank=True, max_length=150, null=True)
    medium_image_url = models.CharField(blank=True, max_length=150, null=True)
    large_image_url = models.CharField(blank=True, max_length=200, null=True)
    is_active = models.BooleanField(default=True)
    asin = models.CharField(blank=True, max_length=15, null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:product", kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart", kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse("core:remove-from-cart", kwargs={
            'slug': self.slug
        })

class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.DO_NOTHING)
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING)
    quantity = models.IntegerField(default=0)
    order = models.ForeignKey('Order', on_delete=models.CASCADE)



    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()

    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()



class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=20, blank=True, null=True)
    items = models.ManyToManyField(Item, through=OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    status = models.CharField(choices=STATUS_CHOICES, default='D', max_length=1)
    shipping_address = models.ForeignKey(
        'BillingAddress', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    billing_address = models.ForeignKey(
        'BillingAddress', related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, blank=True, null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    '''
    1. Item added to cart
    2. Adding a BillingAddress
    (Failed Checkout)
    3. Payment
    4. Being delivered
    5. Received
    6. Refunds
    '''

    def __str__(self):
        return f"id: {self.id} of {self.user.username}"

    def get_total(self):
        total = 0
        for order_item in self.orderitem_set.filter(order=self.id):
            total += order_item.get_final_price()
        if self.coupon:
            total -= self.coupon.amount
        return round(float(total), 2)

    def get_cart_items(self):
        orderitems = self.orderitem_set.filter(order=self.id)
        total = sum([item.quantity for item in orderitems])
        return total

    def get_cart_total(self):
        orderitems = self.orderitem_set.filter(order=self.id)
        total = sum([item.get_final_total for item in orderitems])
        return round(float(total), 2)





class BillingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = 'BillingAddresses'


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.DO_NOTHING, blank=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code


class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"{self.pk}"

class Wishlist(models.Model):
   # here CASCADE is the behavior to adopt when the referenced object(because it is a foreign key) is deleted. it is not specific to django,this is an sql standard.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    wished_item = models.ForeignKey(Item, on_delete=models.CASCADE)
    slug = models.CharField(max_length=30, null=True, blank=True)
    added_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.wished_item.title
    def get_add_to_wishlist_url(self):
        return reverse("core:add-to-wishlist", kwargs={
            'slug': self.slug
        })