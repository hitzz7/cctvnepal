from . import views
from django.urls import path
from django.conf import settings
from django.contrib.sitemaps.views import sitemap
from django.conf.urls.static import static
from .sitemap import ProductSitemap, CategorySitemap, StaticViewSitemap
app_name = 'store'

sitemaps = {
    'products': ProductSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('',views.home, name="home"),
    path('product/', views.product, name='product'),
    path('youtube/', views.youtube, name='youtube'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('product_list/<int:category_id>/', views.product_list, name='product_list'),
    path('product_detail/<slug:slug>/', views.product_detail, name='product_detail'),
    path('project_detail/<int:project_id>/', views.project_detail, name='project_detail'),
     path('services/', views.services, name='services'),
       path('about/', views.about, name='about'),
       path('work/', views.project, name='work'),
         path('contact/', views.contact, name='contact'),
         path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<slug:slug>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<slug:slug>/', views.update_cart, name='update_cart'),
         path('checkout/', views.checkout, name='checkout'),
         path('get-delivery-charge/', views.get_delivery_charge, name='get_delivery_charge'),
     path("packages/", views.package_list, name="package_list"),
    path("packages/<int:pk>/", views.package_detail, name="package_detail"),
        #  path('start /', views.start, name='start'),
         path('contactc/', views.contactc, name='contactc'),
    path('success/', views.success, name='success'),
    path('search/', views.search_products, name='search_products'),
    path('search-page/', views.search_page, name='search_page'),
    path("live/", views.youtube_live, name="youtube_live"),# new
    
    
]

