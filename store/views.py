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
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail


def home(request):

    categories = Category.objects.all()
    projects = Project.objects.all()[:4]
    packages = Package.objects.all()

    # Get Hikvision products
    try:
        hikvision_brand = Brand.objects.get(name__iexact="Hikvision")
        hikvision_products = Product.objects.filter(brand=hikvision_brand)[:4]
    except Brand.DoesNotExist:
        hikvision_products = Product.objects.none()

    # Get Ezviz products
    try:
        ezviz_brand = Brand.objects.get(name__iexact="Ezviz")
        ezviz_products = Product.objects.filter(brand=ezviz_brand)[:4]
    except Brand.DoesNotExist:
        ezviz_products = Product.objects.none()

    # Get site settings for hero image
    from .models import SiteSettings
    site_settings = SiteSettings.objects.first()
    hero_image = site_settings.hero_image if site_settings and site_settings.hero_image else 'hh.png'

    return render(request,'Warzone/home.html',{
        'categories': categories,
        'packages': packages,
        'projects': projects,
        'hikvision_products': hikvision_products,
        'ezviz_products': ezviz_products,
        'hero_image': hero_image
    });


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
    
    # Get similar products from the same category (excluding current product)
    similar_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'images': images,
        'similar_products': similar_products
    }
    return render(request, 'Warzone/productdetail.html', context)

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
            "language": {"code": "en"},
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

    # Get user data if logged in
    user_name = ""
    user_email = ""
    user_phone = ""
    user_address = ""
    user_city_id = ""
    user_landmark = ""
    
    if request.user.is_authenticated:
        user_name = request.user.username
        user_email = request.user.email
        
        # Get latest order for address info
        latest_order = Order.objects.filter(email=user_email).order_by('-id').first()
        if latest_order:
            user_phone = latest_order.phone
            user_address = latest_order.address
            user_city_id = latest_order.city.id if latest_order.city else ""
            user_landmark = latest_order.landmark if latest_order.landmark else ""

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
        
        customer_whatsapp = (
            f"977{order.phone}" if not order.phone.startswith("977") else order.phone
        )
        
        items_text = ", ".join([
            f"{item['product'].title} x {item['quantity']} = NPR {item['subtotal']}"
            for item in cart_items
        ])

        

        # 2️⃣ Build customer info
        customer_info = f"Name: {order.name}; Phone: {order.phone}; Email: {order.email}; Address: {order.address}"
        if order.landmark:
            customer_info += f"; Landmark: {order.landmark}"

        # --------------------------
        # Send WhatsApp Template Message
        # Template needs 5 body params
        # ---
        # Prepare customer WhatsApp number
        
        # List of numbers to send to
        numbers = [
            settings.MY_WHATSAPP_NUMBER,  # your number
            customer_whatsapp            # customer number
        ]

        # Loop and send to each
        for num in numbers:
            send_whatsapp_message(
                to_number=num,
                template_name="order_confirmation",
                components=[
                    {
                        "type": "body", 
                        "parameters": [
                            {"type": "text", "text": order.name},
                            {"type": "text", "text": str(order.id)},
                            {"type": "text", "text": f"NPR {order.total_price}"},
                            {"type": "text", "text": customer_info},
                            {"type": "text", "text": items_text},
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
        "user_name": user_name,
        "user_email": user_email,
        "user_phone": user_phone,
        "user_address": user_address,
        "user_city_id": user_city_id,
        "user_landmark": user_landmark,
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
            whatsapp_message = (
                f"📩 New Contact Message\n\n"
                f"Name: {name}\n"
                f"Email: {email}\n"
                f"Phone: {mobile}\n"
                f"Message: {description}"
            )

            # Send via WhatsApp Cloud API using template
            send_whatsapp_message(
                to_number=settings.MY_WHATSAPP_NUMBER,   # send to your number
                template_name="contact_message",         # create template in WhatsApp
                components=[
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": name},
                            {"type": "text", "text": mobile},
                            {"type": "text", "text": email},
                            {"type": "text", "text": description},
                        ]
                    }
                ]
            )

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

    return render(request, 'Warzone/search_result.html', {
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

def robots_txt(request):
    content = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /accounts/
Disallow: /api/
Sitemap: https://yourdomain.com/sitemap.xml
"""
    return HttpResponse(content, content_type="text/plain")

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'You have successfully logged in!')
            return redirect('store:home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'Warzone/login.html')

def user_logout(request):
    logout(request)
    messages.success(request, 'You have successfully logged out!')
    return redirect('store:home')

def user_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return redirect('store:user_signup')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('store:user_signup')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return redirect('store:user_signup')
        
        user = User.objects.create_user(username=username, email=email, password=password, is_active=False)
        
        # Generate activation token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create activation link
        activation_url = f"{request.scheme}://{request.get_host()}/activate/{uid}/{token}/"
        
        # Send activation email
        subject = 'Activate Your Account - CCTV Nepal'
        message = f'''
Hello {username},

Thank you for signing up at CCTV Nepal!

Please click the link below to activate your account:
{activation_url}

If you did not create this account, please ignore this email.

Best regards,
CCTV Nepal Team
'''
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            messages.success(request, 'Account created! Please check your email to activate your account.')
        except Exception as e:
            messages.error(request, f'Error sending email: {e}')
        
        return redirect('store:user_login')
    
    return render(request, 'Warzone/signup.html')

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, 'Your account has been activated successfully!')
        return redirect('store:home')
    else:
        messages.error(request, 'Invalid activation link or link has expired!')
        return redirect('store:user_login')

@login_required
def user_dashboard(request):
    user = request.user
    orders = Order.objects.filter(email=user.email).order_by('-id')[:10]
    
    # Get most recent order for address info
    latest_order = orders.first() if orders else None
    user_address = None
    user_phone = None
    user_city = None
    
    if latest_order:
        user_address = latest_order.address
        user_phone = latest_order.phone
        user_city = latest_order.city.name if latest_order.city else None
    
    context = {
        'user': user,
        'orders': orders,
        'total_orders': orders.count(),
        'user_address': user_address,
        'user_phone': user_phone,
        'user_city': user_city,
    }
    return render(request, 'Warzone/dashboard.html', context)