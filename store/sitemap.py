from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Category

# Dynamic product pages
class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.date_updated

    def location(self, obj):
        return obj.get_absolute_url()

# Dynamic category pages
class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Category.objects.filter(is_active=True)

    def location(self, obj):
        return obj.get_absolute_url()

# Static pages: About, Services, Contact
class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return ['store:about', 'store:services', 'store:contact','store:home','store:work']

    def location(self, item):
        return reverse(item)
