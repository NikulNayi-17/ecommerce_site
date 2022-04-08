from email import message
from math import sin
from tokenize import single_quoted
from django.core import paginator
from django.db.models.query_utils import Q
from django.http.response import HttpResponse
from cart.views import _cart_id
from cart.models import CartItem
from category.models import Category
from django.shortcuts import get_object_or_404, redirect, render
from orders.models import OrderProduct

from store.forms import ReviewForm
from .models import Product, ProductGallery, ReviewRating
from django.core.paginator import Page, PageNotAnInteger, EmptyPage, Paginator
from django.contrib import messages
# Create your views here.


def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(
            category=categories, is_available=True)
        paginator = Paginator(products, 1)
        page_number = request.GET.get('page')
        paged_proucts = paginator.get_page(page_number)
        product_count = products.count()
    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')
        paginator = Paginator(products, 6)
        page_number = request.GET.get('page')
        paged_proucts = paginator.get_page(page_number)
        product_count = products.count()

    context = {
        'products': paged_proucts,
        'product_count': product_count
    }
    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):

    try:
        single_product = Product.objects.get(
            category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(
            request), product=single_product).exists()
    except Exception as e:
        raise e

    try:
        orderproduct = OrderProduct.objects.filter(
            user=request.user, product_id=single_product.id).exists()
    except OrderProduct.DoesNotExist:
        orderproduct = None

    # get the reviews
    reviews = ReviewRating.objects.filter(
        product_id=single_product.id, status=True)

    # get the product gallery
    product_gallery = ProductGallery.objects.filter(
        product_id=single_product.id)
    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
    }

    return render(request, 'store/product_detail.html', context)


def search(request):
    # if 'keyword' in request.GET:
    keyword = request.GET['keyword']
    if keyword:
        # database quaries
        products = Product.objects.order_by(
            'created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
        product_count = products.count()

        context = {
            'products': products,
            'product_count': product_count
        }
        return render(request, 'store/store.html', context)


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(
                user__id=request.user.id, product_id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(
                request, 'Thank you! your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)

            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = request.POST.get('rating')
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(
                    request, 'Thank you! your review has been submitted.')
                return redirect(url)
