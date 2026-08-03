# admin.py
from django.contrib import admin
from .models import Category, Product, ProductImage,StartaProject,ProjectImage,Project,Brand
from .models import City, Order, OrderItem,Package,SiteSettings
# Define an inline class for ProjectImage
class ProductImageInline(admin.TabularInline):  # You can use StackedInline for a different layout
    model = ProductImage
    extra = 1  # Number of empty forms to display in the admin

# Customize the Project admin
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    list_display = ('title', 'category', 'brand', 'price', 'is_active', 'stock')
    list_filter = ('category', 'brand', 'is_active')
    search_fields = ('title', 'description', 'category__name', 'brand__name')
    # Include the ProjectImage inline in the Project admin
class ProjectImageInline(admin.TabularInline):  # You can use StackedInline for a different layout
    model = ProjectImage
    extra = 1  # Number of empty forms to display in the admin

# Customize the Project admin
class ProjectAdmin(admin.ModelAdmin):
    inlines = [ProjectImageInline] 

# Register your models
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'image')
    list_filter = ('parent',)
    search_fields = ('name',)
    
admin.site.register(Brand)
admin.site.register(Package)
admin.site.register(Product, ProductAdmin)  
admin.site.register(Project, ProjectAdmin) 
admin.site.register(StartaProject)# Use the custom ProjectAdmin
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # do not show extra empty rows
    readonly_fields = ('title', 'price', 'quantity', 'image_url')  # prevent editing if you want
    can_delete = False

# Admin for Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'city', 'total_price', 'is_paid', 'created_at')
    list_filter = ('is_paid', 'city', 'created_at')
    search_fields = ('name', 'email', 'phone', 'address')
    readonly_fields = ('total_price', 'created_at')
    inlines = [OrderItemInline]

# Admin for City
@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'delivery_charge')
    search_fields = ('name',)

# Admin for SiteSettings
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Only allow one instance
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)