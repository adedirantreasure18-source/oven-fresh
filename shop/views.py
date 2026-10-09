from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.http import JsonResponse
from .models import Product, Category, Order, OrderItem, Reservation, ContactMessage
from .forms import CheckoutForm, ReservationForm, ProductForm, OrderStatusForm, StaffUserForm, ContactMessageForm
from .context_processors import Cart
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from datetime import timedelta

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        # Check if user exists AND is either Main Admin or Manager
        if user is not None and (user.is_superuser or user.groups.filter(name__in=['Main Admin', 'Manager']).exists()):
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username, password, or insufficient permissions.')
    
    return render(request, 'login.html')

# --- CUSTOM LOGOUT VIEW ---
def custom_logout(request):
    logout(request)
    return redirect('home')

def home(request):
    bakery_products = Product.objects.filter(category__product_type='bakery', is_available=True)[:6]
    restaurant_products = Product.objects.filter(category__product_type='restaurant', is_available=True)[:6]
    context = {
        'bakery_products': bakery_products,
        'restaurant_products': restaurant_products,
    }
    return render(request, 'home.html', context)


def bakery(request):
    products = Product.objects.filter(category__product_type='bakery', is_available=True)
    categories = Category.objects.filter(product_type='bakery')
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
    context = {
        'products': products,
        'categories': categories,
        'current_category': category_slug,
        'page_type': 'bakery',
    }
    return render(request, 'bakery.html', context)


def restaurant(request):
    products = Product.objects.filter(category__product_type='restaurant', is_available=True)
    categories = Category.objects.filter(product_type='restaurant')
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
    context = {
        'products': products,
        'categories': categories,
        'current_category': category_slug,
        'page_type': 'restaurant',
    }
    return render(request, 'restaurant.html', context)


def about(request):
    return render(request, 'about.html')


def contact(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent! We\'ll get back to you soon.')
            return redirect('contact')
    else:
        form = ContactMessageForm()
    return render(request, 'contact.html', {'form': form})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    related = Product.objects.filter(category=product.category, is_available=True).exclude(id=product.id)[:4]
    context = {'product': product, 'related': related}
    return render(request, 'product_detail.html', context)


def cart_view(request):
    cart = Cart(request)
    return render(request, 'cart.html', {'cart': cart})


def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'login_required': True, 'message': 'Please sign in to add items to your cart.'})
        messages.warning(request, 'Please sign in to add items to your cart.')
        return redirect('customer_login')
    from .models import Product
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart = Cart(request)
    cart.add(product, quantity)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart!',
            'cart_count': len(cart),
            'cart_total': str(cart.get_total_price()),
        })
    messages.success(request, f'{product.name} added to cart!')
    return redirect(request.META.get('HTTP_REFERER', 'cart'))


def remove_from_cart(request, product_id):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please sign in to manage your cart.')
        return redirect('customer_login')
    from .models import Product
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    messages.info(request, 'Item removed from cart')
    return redirect('cart')


def update_cart(request, product_id):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please sign in to update your cart.')
        return redirect('customer_login')
    from .models import Product
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart = Cart(request)
    cart.update_quantity(product, quantity)
    return redirect('cart')


def checkout(request):
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Please sign in to place an order.'})
        messages.warning(request, 'Please sign in to place an order.')
        return redirect('customer_login')
    cart = Cart(request)
    if len(cart) == 0:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Your cart is empty.'})
        messages.warning(request, 'Your cart is empty')
        return redirect('bakery')
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'debit')

        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.total_amount = cart.get_total_price()
            order.payment_method = payment_method
            order.status = 'pending'
            order.save()
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['price'],
                )

            if payment_method == 'debit':
                # Return JSON for Paystack JS to handle
                return JsonResponse({
                    'success': True,
                    'order_id': order.id,
                    'amount': float(order.total_amount),
                })
            else:
                # Bank transfer - complete immediately
                cart.clear()
                messages.success(request, f'Order placed! Transfer details will be sent to your email. Order #{order.order_number}')
                return redirect('order_success', order_id=order.id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Please fill in all required fields correctly.'})
    else:
        form = CheckoutForm()

    return render(request, 'checkout.html', {
        'form': form,
        'cart': cart,
        'cart_total': cart.get_total_price(),
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
    })


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_success.html', {'order': order})


import urllib.request
import json
from django.conf import settings


def verify_paystack_payment(request):
    """Verify Paystack payment and complete order."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})

    reference = request.POST.get('reference')
    order_id = request.POST.get('order_id')

    if not reference or not order_id:
        return JsonResponse({'success': False, 'message': 'Missing payment reference or order ID.'})

    # Verify with Paystack
    url = f'https://api.paystack.co/transaction/verify/{reference}'
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {settings.PAYSTACK_SECRET_KEY}')

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())

        if data['status'] and data['data']['status'] == 'success':
            order = get_object_or_404(Order, id=order_id)
            order.status = 'confirmed'
            order.save()

            # Clear the session cart
            if 'cart' in request.session:
                del request.session['cart']
            if 'pending_order_id' in request.session:
                del request.session['pending_order_id']

            return JsonResponse({
                'success': True,
                'message': f'Payment successful! Order #{order.order_number} confirmed.',
                'order_id': order.id,
                'redirect_url': f'/order/success/{order.id}/',
            })
        else:
            return JsonResponse({'success': False, 'message': 'Payment was not successful. Please try again.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Payment verification failed: {str(e)}'})


def orders_list(request):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please sign in to view your orders.')
        return redirect('customer_login')
    email = request.GET.get('email', '')
    orders = []
    if email:
        orders = Order.objects.filter(email=email)
    return render(request, 'orders.html', {'orders': orders, 'email': email})


def reservation(request):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please sign in to make a reservation.')
        return redirect('customer_login')
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reservation confirmed! We look forward to seeing you.')
            return redirect('reservation_success')
    else:
        form = ReservationForm()
    return render(request, 'reservation.html', {'form': form})


def reservation_success(request):
    return render(request, 'reservation_success.html')


def search(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        results = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_available=True
        )
    return render(request, 'search.html', {'query': query, 'results': results})

@login_required
def dashboard(request):
    user = request.user
    # Check roles
    is_main_admin = user.is_superuser or user.groups.filter(name='Main Admin').exists()
    is_manager = user.groups.filter(name='Manager').exists()
    
    if not (is_main_admin or is_manager):
        messages.error(request, "Access denied. You do not have permission.")
        return redirect('home')
        
    # Analytics Calculations
    total_revenue = Order.objects.filter(
        status__in=['confirmed', 'preparing', 'ready', 'delivered']
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    
    total_orders = Order.objects.count()
    total_products = Product.objects.count()
    pending_reservations = Reservation.objects.filter(date__gte=timezone.now().date()).count()
    recent_orders = Order.objects.select_related().order_by('-created_at')[:5]
    
    # Customer analytics
    total_customers = User.objects.filter(is_staff=False, is_superuser=False).count()
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    new_customers_week = User.objects.filter(is_staff=False, is_superuser=False, date_joined__date__gte=week_ago).count()
    new_customers_month = User.objects.filter(is_staff=False, is_superuser=False, date_joined__date__gte=month_ago).count()
    logged_in_customers = User.objects.filter(is_staff=False, is_superuser=False, last_login__isnull=False).order_by('-last_login')[:10]
    online_now = User.objects.filter(is_staff=False, is_superuser=False, last_login__gte=timezone.now() - timedelta(minutes=30))
    
    # Order status breakdown
    pending_orders = Order.objects.filter(status='pending').count()
    confirmed_orders = Order.objects.filter(status='confirmed').count()
    preparing_orders = Order.objects.filter(status='preparing').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    
    # Revenue this month
    month_revenue = Order.objects.filter(
        status__in=['confirmed', 'preparing', 'ready', 'delivered'],
        created_at__date__gte=month_ago
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    
    context = {
        'is_main_admin': is_main_admin,
        'is_manager': is_manager,
        'role': 'Main Admin' if is_main_admin else 'Manager',
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_products': total_products,
        'pending_reservations': pending_reservations,
        'recent_orders': recent_orders,
        'total_customers': total_customers,
        'new_customers_week': new_customers_week,
        'new_customers_month': new_customers_month,
        'logged_in_customers': logged_in_customers,
        'online_now_count': online_now.count(),
        'online_now': online_now,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'preparing_orders': preparing_orders,
        'delivered_orders': delivered_orders,
        'month_revenue': month_revenue,
    }
    return render(request, 'dashboard.html', context)


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        is_main_admin = request.user.is_superuser or request.user.groups.filter(name='Main Admin').exists()
        is_manager = request.user.groups.filter(name='Manager').exists()
        if not (is_main_admin or is_manager):
            messages.error(request, "Access denied.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required_admin_only(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        is_main_admin = request.user.is_superuser or request.user.groups.filter(name='Main Admin').exists()
        if not is_main_admin:
            messages.error(request, "Admin access only.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ==================== PRODUCT MANAGEMENT ====================

@admin_required
def admin_products(request):
    products = Product.objects.select_related('category').all()
    product_type = request.GET.get('type')
    search = request.GET.get('q', '')
    if product_type:
        products = products.filter(category__product_type=product_type)
    if search:
        products = products.filter(Q(name__icontains=search) | Q(description__icontains=search))
    context = {
        'products': products,
        'product_type': product_type,
        'search': search,
        'is_main_admin': request.user.is_superuser or request.user.groups.filter(name='Main Admin').exists(),
        'is_manager': request.user.groups.filter(name='Manager').exists(),
    }
    return render(request, 'admin_products.html', context)


@admin_required
def admin_product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product created successfully!')
            return redirect('admin_products')
    else:
        form = ProductForm()
    context = {
        'form': form,
        'title': 'Add Product',
        'is_main_admin': request.user.is_superuser or request.user.groups.filter(name='Main Admin').exists(),
        'is_manager': request.user.groups.filter(name='Manager').exists(),
    }
    return render(request, 'admin_product_form.html', context)


@admin_required
def admin_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('admin_products')
    else:
        form = ProductForm(instance=product)
    context = {
        'form': form,
        'product': product,
        'title': 'Edit Product',
        'is_main_admin': request.user.is_superuser or request.user.groups.filter(name='Main Admin').exists(),
        'is_manager': request.user.groups.filter(name='Manager').exists(),
    }
    return render(request, 'admin_product_form.html', context)


@admin_required
def admin_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted.')
        return redirect('admin_products')
    context = {
        'product': product,
        'is_main_admin': request.user.is_superuser or request.user.groups.filter(name='Main Admin').exists(),
        'is_manager': request.user.groups.filter(name='Manager').exists(),
    }
    return render(request, 'admin_product_delete.html', context)


# ==================== ORDER MANAGEMENT ====================

@admin_required
def admin_orders(request):
    orders = Order.objects.all()
    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '')
    if status_filter:
        orders = orders.filter(status=status_filter)
    if search:
        orders = orders.filter(Q(name__icontains=search) | Q(email__icontains=search) | Q(id__icontains=search))
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'search': search,
        'status_choices': Order.STATUS_CHOICES,
        'is_main_admin': request.user.is_superuser or request.user.groups.filter(name='Main Admin').exists(),
        'is_manager': request.user.groups.filter(name='Manager').exists(),
    }
    return render(request, 'admin_orders.html', context)


@admin_required
def admin_order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk)
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f'Order #{order.order_number} status updated.')
            return redirect('admin_orders')
    else:
        form = OrderStatusForm(instance=order)
    context = {
        'order': order,
        'form': form,
        'is_main_admin': request.user.is_superuser or request.user.groups.filter(name='Main Admin').exists(),
        'is_manager': request.user.groups.filter(name='Manager').exists(),
    }
    return render(request, 'admin_order_detail.html', context)


# ==================== RESERVATION MANAGEMENT ====================

@admin_required
def admin_reservations(request):
    reservations = Reservation.objects.all()
    search = request.GET.get('q', '')
    if search:
        reservations = reservations.filter(Q(name__icontains=search) | Q(email__icontains=search))
    context = {
        'reservations': reservations,
        'search': search,
        'is_main_admin': request.user.is_superuser or request.user.groups.filter(name='Main Admin').exists(),
        'is_manager': request.user.groups.filter(name='Manager').exists(),
    }
    return render(request, 'admin_reservations.html', context)


@admin_required
def admin_reservation_detail(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    context = {
        'reservation': reservation,
        'is_main_admin': request.user.is_superuser or request.user.groups.filter(name='Main Admin').exists(),
        'is_manager': request.user.groups.filter(name='Manager').exists(),
    }
    return render(request, 'admin_reservation_detail.html', context)


@admin_required
def admin_reservation_delete(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        reservation.delete()
        messages.success(request, 'Reservation deleted.')
        return redirect('admin_reservations')
    context = {
        'reservation': reservation,
        'is_main_admin': request.user.is_superuser or request.user.groups.filter(name='Main Admin').exists(),
        'is_manager': request.user.groups.filter(name='Manager').exists(),
    }
    return render(request, 'admin_reservation_delete.html', context)


# ==================== USER MANAGEMENT (Admin Only) ====================

@admin_required_admin_only
def admin_users(request):
    users = User.objects.all()
    search = request.GET.get('q', '')
    if search:
        users = users.filter(Q(username__icontains=search) | Q(email__icontains=search) | Q(first_name__icontains=search))
    context = {
        'users': users,
        'search': search,
        'is_main_admin': True,
        'is_manager': False,
    }
    return render(request, 'admin_users.html', context)


@admin_required_admin_only
def admin_user_add(request):
    if request.method == 'POST':
        form = StaffUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            group_name = request.POST.get('group', 'Manager')
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
            messages.success(request, f'User "{user.username}" created successfully!')
            return redirect('admin_users')
    else:
        form = StaffUserForm()
    context = {
        'form': form,
        'groups': Group.objects.all(),
        'is_main_admin': True,
        'is_manager': False,
    }
    return render(request, 'admin_user_form.html', context)


@admin_required_admin_only
def admin_user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.is_superuser = 'is_superuser' in request.POST
        user.is_staff = user.is_superuser
        user.save()
        group_name = request.POST.get('group', 'Manager')
        user.groups.clear()
        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
        messages.success(request, f'User "{user.username}" updated.')
        return redirect('admin_users')
    context = {
        'edit_user': user,
        'groups': Group.objects.all(),
        'is_main_admin': True,
        'is_manager': False,
    }
    return render(request, 'admin_user_edit.html', context)


@admin_required_admin_only
def admin_user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('admin_users')
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted.')
        return redirect('admin_users')
    context = {
        'delete_user': user,
        'is_main_admin': True,
        'is_manager': False,
    }
    return render(request, 'admin_user_delete.html', context)


# ==================== CUSTOMER AUTH ====================

def customer_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect(request.GET.get('next', 'home'))
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'customer_login.html')


def customer_register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        if password != password2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
        else:
            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name
            )
            login(request, user)
            messages.success(request, f'Welcome to Oven Fresh, {first_name or username}!')
            return redirect('home')
    return render(request, 'customer_register.html')


def customer_logout(request):
    logout(request)
    return redirect('home')