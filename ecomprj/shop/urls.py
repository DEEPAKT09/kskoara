from django.urls import path
from . import views
from django.contrib import admin 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name="home"),
    path('home', views.home, name="home"),
    path('login/', views.customer_login, name='login'),  # Customer login
    path('signup', views.signup, name="signup"),
    path('logout', views.logout_page, name="logout"),
    path('userprofile', views.userprofile, name="userprofile"),
    path('about/', views.about, name="about"),
    path('contact', views.contact, name="contact"),
    path('privacypolicy/', views.privacypolicy, name="privacypolicy"),
    path('cart', views.cart_page, name="cart"),
     path('fav',views.fav_page,name="fav"),
    path('favviewpage',views.favviewpage,name="favviewpage"),
    path('remove_fav/<str:fid>',views.remove_fav,name="remove_fav"),
    path('addtocart',views.add_to_cart,name="add_to_cart"),
    path('remove_cart/<str:cid>',views.remove_cart,name="remove_cart"),
    path('productssidebar/<str:name>', views.productssidebar, name="productssidebar"),
    path('productsinfo/<str:cname>/<str:pname>',views.productsinfo, name="productsinfo"),
    path('order_confirmation/<int:order_id>', views.order_confirmation, name='order_confirmation'),
    path('checkout/',views.checkout, name="checkout"),
    path('track-order/', views.track_order, name='track_order'),
    path('payment-verification/', views.payment_verification, name='payment_verification')
 ] 