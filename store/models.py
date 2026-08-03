from django.db import models
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
# Create your models here.
class Category(MPTTModel):
    """
    Category Table implimented with MPTT.
    """

    name = models.CharField(
        verbose_name=_("Category Name"),
        help_text=_("Required and unique"),
        max_length=255,
        unique=True,
    )

    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    is_active = models.BooleanField(default=True)


    class MPTTMeta:
        order_insertion_by = ["name"]

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")


    def get_absolute_url(self):
        return reverse("store:product") + f"?category={self.id}"

    # def get_absolute_url(self):
    #     return reverse("store:category_list", args=[self.slug])

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    

    def __str__(self):
        return self.name
        
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.RESTRICT,related_name='product')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=255,blank=True, null=True)
    date_created = models.DateField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    on_sale = models.BooleanField(default=False)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pdf_document = models.FileField(upload_to='product_pdfs/', blank=True, null=True)  
    
    

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            num = 1

            # Ensure slug is unique
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1

            self.slug = slug
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        
        return reverse("store:product_detail", args=[self.slug])
    
    
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_feature = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.product.title}"
    
class Project(models.Model):
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    date_created = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title

class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='projects/')
    is_feature = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.project.title}"

    
    
class StartaProject(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=150)
    description = models.TextField(blank=False)
    
    def __str__(self):
        return self.name
    
class City(models.Model):
    name = models.CharField(max_length=100)
    delivery_charge = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name    

class Order(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)
    landmark = models.TextField(default='', blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.id} - {self.name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    image_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.title} (x{self.quantity})"
    
    
class Package(models.Model):
    name = models.CharField(max_length=100)        # e.g. "Basic Package"
    price = models.DecimalField(max_digits=10, decimal_places=2)  # e.g. 5999.00
    features = models.TextField()                  # store features as text or bullet list

    def __str__(self):
        return f"{self.name} - Rs {self.price}"


class SiteSettings(models.Model):
    hero_image = models.ImageField(upload_to='hero/', blank=True, null=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return "Site Configuration"