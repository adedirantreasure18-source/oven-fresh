from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('bakery/', views.bakery, name='bakery'),
    path('restaurant/', views.restaurant, name='restaurant'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('payment/verify/', views.verify_paystack_payment, name='verify_paystack_payment'),
    path('orders/', views.orders_list, name='orders'),
    path('reservation/', views.reservation, name='reservation'),
    path('reservation/success/', views.reservation_success, name='reservation_success'),
    path('search/', views.search, name='search'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),

    # Customer auth
    path('account/login/', views.customer_login, name='customer_login'),
    path('account/register/', views.customer_register, name='customer_register'),
    path('account/logout/', views.customer_logout, name='customer_logout'),

    # Admin panel
    path('panel/products/', views.admin_products, name='admin_products'),
    path('panel/products/add/', views.admin_product_add, name='admin_product_add'),
    path('panel/products/<int:pk>/edit/', views.admin_product_edit, name='admin_product_edit'),
    path('panel/products/<int:pk>/delete/', views.admin_product_delete, name='admin_product_delete'),
    path('panel/orders/', views.admin_orders, name='admin_orders'),
    path('panel/orders/<int:pk>/', views.admin_order_detail, name='admin_order_detail'),
    path('panel/reservations/', views.admin_reservations, name='admin_reservations'),
    path('panel/reservations/<int:pk>/', views.admin_reservation_detail, name='admin_reservation_detail'),
    path('panel/reservations/<int:pk>/delete/', views.admin_reservation_delete, name='admin_reservation_delete'),
    path('panel/users/', views.admin_users, name='admin_users'),
    path('panel/users/add/', views.admin_user_add, name='admin_user_add'),
    path('panel/users/<int:pk>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('panel/users/<int:pk>/delete/', views.admin_user_delete, name='admin_user_delete'),
]