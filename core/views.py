import csv
import json
import os
import hashlib
import uuid
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from django.db.models import Q
import pandas as pd
import random
import string
import smtplib
# import urllib.requestx
import subprocess
import stripe
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView, View
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from .forms import CheckoutForm, CouponForm, RefundForm, PaymentForm
from .models import Item, OrderItem, Order, Coupon, Refund, UserProfile, Brand, Category, SubCategory, ItemImage


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
            try:
                order = get_object_or_404(Order, user=self.request.user, payment=False)
            except:
                order = get_object_or_404(Order, session_id=self.request.session['nonuser'], payment=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }
            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            try:
                order = get_object_or_404(Order, user=self.request.user, payment=False)
            except:
                order = get_object_or_404(Order, session_id=self.request.session['nonuser'], payment=False)
            items = order.items.get_queryset()
            print(items)
            # df = pd.DataFrame(columns=['Title', 'Quantity', 'Sum'])
            # # pd.concat([df([item.item.title, item.quantity, item.get_final_price()], columns=['Title', 'Quantity', 'Sum']) for item in items],
            # #           ignore_index=True)
            # for item in items:
            #     df1 = pd.DataFrame({'Title': [item.item.title], 'Quantity': [item.quantity], 'Sum': [item.get_final_price()]})
            #     df = df.append(df1, ignore_index=True)
            #     df.index+=1
            if form.is_valid():
                # print("User is entering a new shipping address")
                shipping_address = form.cleaned_data.get('shipping_address')
                phone_number = form.cleaned_data.get('phone_number')
                comment = form.cleaned_data.get('comment')
                print(shipping_address)
                print(phone_number)
                print(comment)
                subprocess.call("php core\\smt.php " + str(order.id) + " " + str(int(order.get_total())), shell=True)
                print(os.path.exists("\\core\\testfile.txt"))
                content = ""
                with open("core\\testfile.txt") as f:
                    content = f.readlines()
                print(content)
                request = {
                    'pg_order_id': order.id,
                    'pg_merchant_id': "550089",
                    'pg_amount': int(order.get_total()),
                    'pg_description': "test",
                    'pg_salt': "599.kz",
                    'pg_success_url': 'http://127.0.0.1:8000/successPayment/',
                    'pg_failure_url': 'http://127.0.0.1:8000/checkout/',
                    'pg_success_url_method': 'GET',
                    'pg_failure_url_method': 'GET',
                    'pg_sig': content[0],
                }
                print(request)
                result = requests.post('https://api.freedompay.money/init_payment.php', params=request)
                print(result)
                sg = ""
                result = str(result.text)
                print(result)
                for i in range(10, len(result)):
                    if result[i] == 'l' and result[i + 1] == '>':
                        print('gfdsgdfg')
                        i += 2
                        while result[i] != '<':
                            sg += result[i]
                            i += 1
                        break
                return redirect(sg)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")

def SuccesPayment(request):
    order = Order.objects.get(id=request.GET.get('pg_order_id'), payment=False)
    # order_items = order.items.all()
    # order_items.update(payment=True)
    # for item in order_items:
    #     item.save()
    order.ordered_date = timezone.now()
    order.payment = True
    order.ref_code = create_ref_code()
    order.save()
    messages.success(request, "Your order was successful!")
    return redirect("/")


@csrf_exempt
def home1(request, ctg, ctg2):
    if ctg2 != 'all':
        object_list = Item.objects.filter(category__title=ctg, subcategory__title=ctg2)
    else:
        object_list = Item.objects.filter(category__title=ctg)
    paginator = Paginator(object_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    categories = Category.objects.all()
    context = {
        'category': Category.objects.filter(title=ctg)[0],
        'object_list': page_obj,
        'user': request.user,
        'categories': categories,
    }
    return render(request, 'shop.html', context)

@login_required
def orders(request):
    categories = Category.objects.all()
    orders = Order.objects.filter(user=request.user, payment=True)
    return render(request, 'orders.html', {'user': request.user, 'orders': orders,'categories': categories,})

@login_required
def profile(request):
    categories = Category.objects.all()
    if request.method == "POST":
        cnt = 0
        if len(User.objects.filter(username=request.POST['username'])) > 0 and request.POST[
            'username'] != request.user.username:
            messages.info(request, 'User already exists')
            cnt = 1
        if len(request.POST['password1']) > 0:
            if len(request.POST['password1']) < 8:
                messages.info(request, 'Password must contain at least 8 symbols')
                cnt = 1
            if len(request.POST['password1']) and len(request.POST['password2']) and request.POST['password1'] != \
                    request.POST['password2']:
                messages.info(request, 'Password not matching')
                cnt = 1
            if len(request.POST['password1']) < 8 and request.POST['password1'] == request.POST['password2']:
                pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).+$'
                if not re.match(pattern, password1):
                    messages.info(request, "Password must contain at least 1 uppercase, 1 lowercase and one number")
                    cnt = 1
        if cnt == 1:
            return redirect('core:edit_profile')
        else:
            if len(request.POST['password1']) > 0 and len(request.POST['password2']) > 0:
                request.user.password1 = request.POST['password1']
                request.user.password2 = request.POST['password2']

            request.user.username = request.POST['username']
            request.user.email = request.POST['email']
            request.user.first_name = request.POST['first_name']
            request.user.last_name = request.POST['first_name']
            request.user.save()
            messages.success(request, "Account was created successfully")
            return redirect('core:profile')
    print(request.user.username)
    return render(request, 'profile.html', {'user': request.user,'categories': categories})

@csrf_exempt
def home(request):
    search = False
    list = []
    if not _user_is_authenticated(request.user):
        try:
            print(request.session['nonuser'])
        except:
            request.session['nonuser'] = str(uuid.uuid4())
            print('dfgdfgdfgdfg')
            print(request.session['nonuser'])
    if request.method == 'POST':
        input = request.POST.get('search')
        input1 = input[0].upper() + input[1:]
        list = Item.objects.filter(Q(title__icontains=input) | Q(acrtiul__icontains=input) | Q(title__icontains=input.upper()) | Q(title__icontains=input1))
        search = True
    categories = Category.objects.all()
    items = Item.objects.all()
    context = {
        'items': items,
        'search': search,
        'searching_list': list,
        'categories': categories,
    }
    # print(page_obj)
    return render(request, 'carousel.html', context)

@login_required
def add_to_cart1(request):
    print(12312)
    try:
        slug = str(request.POST.get('slug'))
        print(slug)
        item = get_object_or_404(Item, slug=slug)
        order_item, created = OrderItem.objects.get_or_create(
            item=item,
            user=request.user,
            ordered=False
        )
        order_qs = Order.objects.filter(user=request.user, payment=False)
        if order_qs.exists():
            order = order_qs[0]
            if order.items.filter(item__slug=item.slug).exists():
                order_item.quantity += 1
                order_item.save()
                messages.info(request, "This item quantity was updated.")
            else:
                order.items.add(order_item)
                messages.info(request, "This item was added to your cart.")
        else:
            ordered_date = timezone.now()
            order = Order.objects.create(
                user=request.user, ordered_date=ordered_date)
            order.items.add(order_item)
            messages.info(request, "core:order-summary")
        return JsonResponse({'data': '123'})
    except:
        slug = str(request.POST.get('slug'))
        print(

        )
        print(slug)
        item = get_object_or_404(Item, slug=slug)
        order_item, created = OrderItem.objects.get_or_create(
            item=item,
            session_id=request.session['nonuser'],
            ordered=False
        )
        order_qs = Order.objects.filter(session_id=request.session['nonuser'], payment=False)
        if order_qs.exists():
            order = order_qs[0]
            if order.items.filter(item__slug=item.slug).exists():
                order_item.quantity += 1
                order_item.save()
                messages.info(request, "This item quantity was updated.")
            else:
                order.items.add(order_item)
                messages.info(request, "This item was added to your cart.")
        else:
            ordered_date = timezone.now()
            order = Order.objects.create(
                session_id=request.session['nonuser'], ordered_date=ordered_date)
            order.items.add(order_item)
            messages.info(request, "core:order-summary")
        return JsonResponse({'data': '123'})

def replace(arr):
    ans = []
    sum = 0
    for i in arr:
        sum+=i
    for i in arr:
        try:
            ans.append(round(i/sum*100))
        except:
            ans.append(0)
    return ans

def clear_cart(request):
    try:
        try:
            order = Order.objects.filter(user=request.user, payment=False)[0]
            for order_item in order.items.get_queryset():
                order.items.remove(order_item)
                order_item.delete()
            return redirect("/")
        except ObjectDoesNotExist:
            messages.warning(request, "You do not have an active order")
            return redirect("/")
    except:
        order = Order.objects.filter(session_id=request.session['nonuser'],payment=False)[0]
        for order_item in order.items.get_queryset():
            order.items.remove(order_item)
            order_item.delete()
        order.save()
        return redirect("/")


def _user_is_authenticated(user):
    # django < 2.0
    try:
        return user.is_authenticated()
    except TypeError:
        # django >= 2.0
        return user.is_authenticated

@login_required
def order_summary(request):
    categories = Category.objects.all()
    try:
        order = Order.objects.filter(user=request.user, payment=False)[0]
    except:
        order = Order.objects.create(user=request.user, payment=False)
    print(request.user)
    context = {
        'order': order,
        'categories': categories,
    }
    return render(request, 'order_summary.html', context)



def detail(request, slug):
    item = Item.objects.filter(slug=slug)[0]
    images = ItemImage.objects.filter(post__slug=slug)
    print(12312313)
    # print(images[0].images)
    context = {
        'description': item.description.split('\n'),
        'item': item,
        'images': images
    }
    return render(request, 'detail.html', context)


def detail_next(request, slug):
    if len(Item.objects.all()) > int(slug[4:])+1:
        slug = 'item' + str(int(slug[4:])+1)
    item = Item.objects.filter(slug=slug)[0]
    images = ItemImage.objects.filter(post__slug=slug)
    context = {
            'object': item,
            'images': images
        }
    return render(request, 'detail.html', context)


def detail_prev(request, slug):
    if int(slug[4:]) > 1:
        slug = 'item' + str(int(slug[4:])-1)
    item = Item.objects.filter(slug=slug)[0]
    images = ItemImage.objects.filter(post__slug=slug)
    context = {
            'object': item,
            'images': images
        }
    return render(request, 'detail.html', context)
def add_to_cart(request, slug):
    print(123)
    user = request.user
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=user,

    )
    order_qs = Order.objects.filter(user=user, payment=False)
    print(order_qs)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("core:order-summary")

    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "core:order-summary")
        return redirect("/")


def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    try:
        order_qs = Order.objects.filter(
            user=request.user,
            payment=False,
        )
    except:
        order_qs = Order.objects.filter(
            session_id=request.session['nonuser'],
            payment=False,
        )

    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            try:
                order_item = OrderItem.objects.filter(
                    item=item,
                    user=request.user,
                    ordered=False
                )[0]
            except:
                order_item = OrderItem.objects.filter(
                    item=item,
                    session_id=request.session['nonuser'],
                    ordered=False
                )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    try:
        order_qs = Order.objects.filter(
            user=request.user,
            payment=False
        )
    except:
        order_qs = Order.objects.filter(
            session_id=request.session['nonuser'],
            payment=False,
        )

    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            try:
                order_item = OrderItem.objects.filter(
                    item=item,
                    user=request.user,
                    ordered=False
                )[0]
            except:
                order_item = OrderItem.objects.filter(
                    item=item,
                    session_id=request.session['nonuser'],
                    ordered=False
                )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


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
                    user=self.request.user, ordered=False)
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

                messages.info(self.request, "Your request was received.")
                return redirect("core:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist.")
                return redirect("core:request-refund")
# data = {
#                     'pg_order_id': order.id,
#                     'pg_merchant_id': "545774",
#                     'pg_amount': int(order.get_total()),
#                     'pg_description': "test",
#                     'pg_salt': "ybeauty",
#                     'pg_sig': content,
#                     'pg_success_url': 'http://ybeauty.kz:81/successPayment/',
#                     'pg_failure_url': 'http://ybeauty.kz:81/checkout/',
#                     'pg_success_url_method': 'GET',
#                     'pg_failure_url_method': 'GET',
#                 }