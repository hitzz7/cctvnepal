from django.shortcuts import render
from .models import Category,Project,ProjectImage,Product,ProductImage,Brand
from django.shortcuts import render, get_object_or_404
from django.shortcuts import render, redirect
from .forms import ContactForm
from django.core.mail import send_mail
from django.conf import settings
from .models import Order, OrderItem, City
from django.contrib import messages
import json
from django.http import JsonResponse
from django.db.models import Q
from twilio.rest import Client
from decimal import Decimal
import requests
from .models import Package
from django.core.mail import send_mail


def home(request):
    
    categories = Category.objects.all()
    products = Product.objects.all()[:4]
    projects = Project.objects.all()[:4]
    packages = Package.objects.all()
    
    try:
        hikvision_brand = Brand.objects.get(name__iexact="Hikvision")
        products = Product.objects.filter(brand=hikvision_brand)[:4]
    except Brand.DoesNotExist:
        products = Product.objects.none()
        
    return render(request,'Warzone/home.html',{'categories': categories,"packages": packages,'projects':projects,'products':products});


def package_list(request):
    packages = Package.objects.all()
    return render(request, "packages/package_list.html", {"packages": packages})

def package_detail(request, pk):
    package = get_object_or_404(Package, pk=pk)
    return render(request, "packages/package_detail.html", {"package": package})

def product(request):
    # Show only top-level categories
    categories = Category.objects.filter(parent=None)
    brand_param = request.GET.get('brand')
    category_id = request.GET.get('category')
    selected_category = None
    child_categories = []
    brand_name = None 
    products = Product.objects.all()
    selected_brand = None

    if category_id:
        try:
            selected_category = Category.objects.get(id=category_id)
            # Include products from selected category + all its descendants
            category_ids = selected_category.get_descendants(include_self=True).values_list('id', flat=True)
            products = Product.objects.filter(category_id__in=category_ids)
            # Get immediate children of selected category
            child_categories = selected_category.get_children()
        except Category.DoesNotExist:
            products = Product.objects.all()
            
    if brand_param:
        try:
            selected_brand = Brand.objects.get(name__iexact=brand_param.strip())
            products = products.filter(brand=selected_brand)
            brand_name = selected_brand.name  # send to template
        except Brand.DoesNotExist:
            selected_brand = None
            brand_name = None


    context = {
        'categories': categories,
        'products': products,
        
        'selected_category': selected_category,
        'child_categories': child_categories,
        'selected_brand': selected_brand,
        'brand_name': brand_name,
        
    }

    return render(request, 'Warzone/product.html', context)

def project(request):
    projects = Project.objects.all()
    
    return render(request, 'Warzone/work.html', {'projects': projects})

def project_detail(request,project_id):
    project = get_object_or_404(Project,pk=project_id)
    images = project.images.all()
    return render(request,'Warzone/projectdetail.html',{'project':project,'images':images})
    
    
def cart_item_count(request):
    cart = request.session.get('cart', {})
    item_count = sum(cart.values())
    return {'cart_item_count': item_count}


def product_list(request):
    category_id = request.GET.get('category')
    categories = Category.objects.all()
    
    if category_id:
        products = Product.objects.filter(category_id=category_id)
    else:
        products = Product.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': int(category_id) if category_id else None
    }
    return render(request, 'store/products.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    images = product.images.all()  # Uses the related_name 'images'
    return render(request, 'Warzone/productdetail.html', {'product': product, 'images': images})

def services(request):
    return render(request, 'Warzone/services.html')
def youtube(request):
    return render(request, 'Warzone/youtube.html')
def work(request):
    return render(request, 'Warzone/work.html')
def about(request):
    return render(request, 'Warzone/about.html')
def contact(request):
    return render(request, 'Warzone/contact.html')

def cart_detail(request):
    cart = request.session.get('cart', {})
    
    
    
    
    cart_items = []
    total_price = 0

    for product_id, item in cart.items():
        product = get_object_or_404(Product, id=product_id)
        subtotal = product.discount_price * item['quantity']
        total_price += subtotal
        
        feature_image = product.images.filter(is_feature=True).first()
        
        cart_items.append({
            'product': product,
            'quantity': item['quantity'],
            'subtotal': subtotal,
            'feature_image': feature_image.image.url if feature_image else None,
        })
        

    context = {
        'cart_items': cart_items,
        'total_price': total_price
        
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, 'Warzone/cart.html', context)
    return render(request, 'Warzone/cart.html', context)

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})

    if request.method == "POST":
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity < 1:
                quantity = 1
        except ValueError:
            quantity = 1

        # Add or update cart item
        if str(product.id) in cart:
            cart[str(product.id)]['quantity'] += quantity
        else:
            cart[str(product.id)] = {
                'quantity': quantity,
                'price': str(product.discount_price or product.price)
            }

        request.session['cart'] = cart

        # Calculate total cart item count
        total_items = sum(item['quantity'] for item in cart.values())

        # --- If it's an AJAX request ---
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': total_items,
            })

    # Normal (non-AJAX) fallback
    return redirect('store:product_detail', product.slug)

def remove_from_cart(request, slug):
    product = get_object_or_404(Product, slug=slug)
    cart = request.session.get('cart', {})

    # Convert product ID to string (since session keys are strings)
    product_id = str(product.id)

    if product_id in cart:
        del cart[product_id]
        request.session['cart'] = cart

    return redirect('store:product_detail', slug=slug)


def update_cart(request, slug):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        product = get_object_or_404(Product, slug=slug)
        cart = request.session.get('cart', {})

        product_id = str(product.id)

        if product_id in cart:
            if quantity > 0:
                cart[product_id]['quantity'] = quantity
            else:
                del cart[product_id]
            request.session['cart'] = cart

    return redirect('store:product_detail', slug=slug)

def get_delivery_charge(request):
    city_id = request.GET.get("city_id")
    if city_id:
        try:
            city = City.objects.get(id=city_id)
            return JsonResponse({"delivery_charge": city.delivery_charge})
        except City.DoesNotExist:
            pass
    return JsonResponse({"delivery_charge": 0})

def send_whatsapp_message_twilio(to_number, message_body):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    message = client.messages.create(
        body=message_body,
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        to=to_number
    )
    
    
    print("Message SID:", message.sid)
    return(message.sid)

def send_whatsapp_message(to_number, template_name=None, components=None):
    """
    Send WhatsApp message using a pre-approved template via Meta Cloud API.
    """
    

    url = f"https://graph.facebook.com/v17.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_CLOUD_TOKEN}",
        "Content-Type": "application/json",
    }

    if not template_name:
        print("⚠️ Template name is required for templated messages.")
        return None

    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        
        "template": {
            "name": template_name,  # e.g., 'order_confirmation'
            "language": {"code": "en_US"},
        },
    }

    # If your template has placeholders, add dynamic components
    if components:
        data["template"]["components"] = components

    response = requests.post(url, headers=headers, json=data)
    print("📤 WhatsApp API Response:", response.json())
    return response.json()

def checkout(request):
    cities = City.objects.all()
    cart = request.session.get("cart", {})

    cart_items = []
    total_price = 0

    for product_id, item in cart.items():
        product = get_object_or_404(Product, id=product_id)
        quantity = item["quantity"]
        price = float(item["price"])
        subtotal = price * quantity
        total_price += subtotal

        feature_image = product.images.filter(is_feature=True).first()
        img_url = feature_image.image.url if feature_image else ""

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
            "feature_image": img_url,
        })

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        city_id = request.POST.get("city")
        landmark = request.POST.get("landmark", "")

        if not cart:
            messages.error(request, "Your cart is empty!")
            return redirect("store:product_list")

        city = City.objects.get(id=city_id) if city_id else None
        delivery_charge = city.delivery_charge if city else 0
        total_with_delivery = Decimal(total_price) + delivery_charge

        # Create order
        order = Order.objects.create(
            name=name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            landmark=landmark,
            total_price=total_with_delivery
        )

        # Save order items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                title=item["product"].title,
                price=item["product"].price,
                quantity=item["quantity"],
                image_url=item["feature_image"]
            )

        # Clear session cart
        request.session["cart"] = {}
        messages.success(request, f"Order placed successfully! Your order ID is {order.id}")
        message_text = f"✅ Order Confirmation\n\n"
        message_text += f"Order ID: {order.id}\n"
        message_text += f"Name: {order.name}\n"
        message_text += f"Phone: {order.phone}\n"
        message_text += f"Email: {order.email}\n"
        message_text += f"Address: {order.address}, {order.city.name if order.city else ''}\n"
        if order.landmark:
            message_text += f"Landmark: {order.landmark}\n"
        message_text += f"\n🛒 Items:\n"
        
        email_body = f"Order Confirmation\n\nOrder ID: {order.id}\nName: {order.name}\nPhone: {order.phone}\nEmail: {order.email}\nAddress: {order.address}, {order.city.name if order.city else ''}\n"

        for item in cart_items:
            message_text += f"- {item['product'].title} x {item['quantity']} = NPR {item['subtotal']}\n"
            email_body += f"- {item['product'].title} x {item['quantity']} = NPR {item['subtotal']}\n"

        message_text += f"\nTotal (with delivery): NPR {order.total_price}"

        # Send WhatsApp message
        send_whatsapp_message(
            to_number=settings.MY_WHATSAPP_NUMBER,  # or customer's number
            template_name="order_confirmation",  # must match approved template name
            components=[
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": order.name},
                        {"type": "text", "text": str(order.id)},
                        {"type": "text", "text": f"NPR {order.total_price}"},
                    ],
                }
            ],
        )

        
        # customer_whatsapp = f"977{phone}" if not phone.startswith("977") else phone
        # send_whatsapp_message(customer_whatsapp, message_text)
        
        send_mail(
            subject="Your Order Confirmation",
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

 # replace with your number or customer's number

        return redirect("store:success")
    # Pass cart data to template
    context = {
        "cities": cities,
        "cart_items": cart_items,
        
        "total_price": total_price,
    }
    return render(request, "Warzone/checkout.html", context)




    

    
def contactc(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Save the form data to the database
            form.save()

            # Get the form data to send in the email
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            mobile = form.cleaned_data['mobile']
            description = form.cleaned_data['description']
            
            # Compose the email content
            subject = f'New Contact Message from {name}'
            message = f"Name: {name}\nEmail: {email}\nPhone: {mobile}\nMessage: {description}"
            recipient_email = 'najus777@gmail.com'  # Replace with the recipient's email address
            
            try:
                # Send the email using Django's send_mail function
                send_mail(subject, message, settings.EMAIL_HOST_USER, [recipient_email])

                # Redirect to success page or any other appropriate page
                return redirect('Warzone:success')  # You can change 'Warzone:success' to your actual success URL
            except Exception as e:
                # Handle any errors that occur while sending the email
                print(f"Error sending email: {e}")
                return render(request, 'Warzone/contact.html', {'form': form, 'error': 'There was an error sending the email. Please try again.'})

    else:
        form = ContactForm()

    return render(request, 'Warzone/contact.html', {'form': form})
def success(request):
    # Get the last placed order for this user/session
    order = Order.objects.last()  # or use session key if available

    if not order:
        return render(request, 'Warzone/success.html', {
            'order': None,
            'order_items': [],
        })

    order_items = order.items.all()  # if related_name='items' in OrderItem model

    return render(request, 'Warzone/success.html', {
        'order': order,
        'order_items': order_items,
    })
    
def search_products(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    ) if query else Product.objects.none()

    return render(request, 'Warzone/search_results.html', {
        'products': products,
        'query': query
    })
    
def search_page(request):
    return render(request, 'Warzone/search_page.html')

def youtube_live(request):
    # You will replace these in the template
    context = {
        "YOUTUBE_API_KEY": "YOUR_API_KEY",
        "CHANNEL_ID": "YOUR_CHANNEL_ID",
    }
    return render(request, "youtube_live.html", context)