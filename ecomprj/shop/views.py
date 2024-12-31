from django.shortcuts import redirect, render
from django.utils.timezone import make_aware
import razorpay
from . models import *
from django.urls import reverse
from django.db import transaction
from django.contrib import messages
from datetime import datetime, timedelta
from django.contrib.auth import authenticate, login , logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Customer
from .form import CustomerUserForm
from django.conf import settings

# Helper function to check if the user is an admin
def is_admin(user):
    return user.is_staff

def home(request):
    category = Category.objects.filter(status=0)
    # Group products by name, taking the latest product for each group (based on SKU)
    main_products_queryset = (
        Product.objects.filter(size_format='SIZE')
        .values('name')
        .annotate(latest_sku=Max('sku'))
    )

     # Extract SKUs in Python
    latest_skus = [item['latest_sku'] for item in main_products_queryset]

    # Fetch all products corresponding to the SKUs
    all_main_products = list(Product.objects.filter(sku__in=latest_skus))

    # Limit to 4 main products
    main_products = all_main_products[:4]

    # Fetch 4 random products excluding the main products
    excluded_skus = [product.sku for product in main_products]
    random_products = Product.objects.exclude(sku__in=excluded_skus).order_by('?')[:4]

        # Fetch trending products and order by creation date
    trending_products_queryset = Product.objects.filter(trending=True).order_by('-created_at')[:50]

    # Deduplicate by name in Python
    unique_trending_products = []
    seen_names = set()

    for product in trending_products_queryset:
        if product.name not in seen_names:
            unique_trending_products.append(product)
            seen_names.add(product.name)
        if len(unique_trending_products) == 8:
            break

    trending_products = unique_trending_products

    return render(request, "shop/index.html", {
        "category": category,
        "main_products": main_products,
        "random_products": random_products,
        "trending_products": trending_products,

    })

def customer_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)

        if user is not None and not user.is_staff:
            login(request, user)
            messages.success(request, "Logged in successfully.")
            return redirect('home')
        else:
            messages.error(request, "Invalid credentials.")
    return render(request, 'shop/login.html')


def signup(request):
    form = CustomerUserForm()
    if request.method == 'POST':
        form = CustomerUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # Save the user instance without committing
            user.set_password(form.cleaned_data['password1'])  # Set the password
            user.save()  # Save the user
            messages.success(request, "Account created successfully!")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    return render(request, 'shop/create-account.html', {'form': form})

def about(request):
    return render(request, 'shop/about.html')

def privacypolicy(request):
    return render(request, 'shop/privacy.html')

def contact(request):
    return render(request, 'shop/contact-us.html')

def logout_page(request):
     logout(request)
     messages.success(request, "Logged out successfully!")
     return redirect('/')  # Redirect to login page after logout

@login_required(login_url='login')  # Ensure the user is logged in
def userprofile(request):
    # Fetch user details
    user = request.user

    # Fetch all orders placed by the user
    user_orders = Orders.objects.filter(customer=user).order_by('-created_at')

    # Pass data to the template
    return render(request, "shop/user-profile.html", {
        'user': user,
        'user_orders': user_orders,
    })


def cart_page(request):
  if request.user.is_authenticated:
    cart=Cart.objects.filter(user=request.user)
    return render(request,"shop/cart.html",{"cart":cart})
  else:
    return redirect("/")
 
def remove_cart(request,cid):
  cartitem=Cart.objects.get(id=cid)
  cartitem.delete()
  return redirect("/cart")

def fav_page(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.user.is_authenticated:
            data = json.loads(request.body)
            product_sku = data.get('sku')  # Use 'sku' instead of 'id'
    
            # Ensure SKU is provided
            if not product_sku:
                return JsonResponse({'status': 'SKU is missing'}, status=400)

            try:
                # Look up the product using SKU (not id)
                product = Product.objects.get(sku=product_sku)  # Use sku here

                # Handle favourite logic here (check if product is already favourited)
                fav, created = Favourite.objects.get_or_create(user=request.user, product=product)

                if created:
                    return JsonResponse({'status': 'Product added to favourites!'}, status=200)
                else:
                    return JsonResponse({'status': 'Product already in favourites!'}, status=200)

            except Product.DoesNotExist:
                return JsonResponse({'status': 'Product not found'}, status=404)
        else:
            return JsonResponse({'status': 'Login to Add Favourite'}, status=200)
    else:
        return JsonResponse({'status': 'Invalid Access'}, status=200)


@login_required(login_url='login')   
def favviewpage(request):
  if request.user.is_authenticated:
    fav=Favourite.objects.filter(user=request.user)
    return render(request,"shop/wishlist.html",{"fav":fav})
  else:
    return redirect("/")
  
def remove_fav(request,fid):
  item=Favourite.objects.get(id=fid)
  item.delete()
  return redirect("/favviewpage")

# Function to extract the base SKU (without size)
def extract_sku_parts(full_sku):
    # Split the SKU into parts by the '-' delimiter
    parts = full_sku.split('-')
    # Exclude the size (last part) to get the base SKU
    base_sku = '-'.join(parts[:-1])  # Join all parts except the last one (size)
    return base_sku

@login_required
def add_to_cart(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            product_qty = int(data.get('product_qty'))
            product_sku = data.get('sku')
            selected_size = data.get('size')  # Get the selected size

            # Store the selected size in the session
            request.session['selected_size'] = selected_size
            # Log the received SKU for debugging
            print("Received SKU:", product_sku)
            print("Received data:", data)
            print("Selected Size:", selected_size)

            if not product_sku: 
                return JsonResponse({'status': 'SKU is required'}, status=400)

            # Use the SKU to find the product
            product = Product.objects.get(sku=product_sku)

            # Check if the product is already in the cart
            if Cart.objects.filter(user=request.user, product=product).exists():
                return JsonResponse({'status': 'Product already in cart'}, status=200)

            # Check stock and add to cart
            if product.quantity >= product_qty:
                Cart.objects.create(user=request.user, product=product, product_qty=product_qty, selected_size=selected_size,)
                return JsonResponse({'status': 'Product added to cart'}, status=200)
            else:
                return JsonResponse({'status': 'Insufficient stock'}, status=400)

        except KeyError:
            return JsonResponse({'status': 'Bad Request. SKU and Quantity are required.'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'Invalid JSON data'}, status=400)
        except Product.DoesNotExist:
            # Add error handling if the product is not found
            return JsonResponse({'status': 'Product not found for SKU: ' + product_sku}, status=404)

    return JsonResponse({'status': 'Invalid Request'}, status=400)

def track_order(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order_date = request.POST.get('order_date')

        try:
            # Convert string date to datetime for comparison
            naive_order_date = datetime.strptime(order_date, '%Y-%m-%d')
            aware_order_date = make_aware(naive_order_date)  # Make it timezone-aware

            # Retrieve the order
            order = get_object_or_404(Orders, id=order_id, created_at__date=aware_order_date.date())
            return render(request, 'shop/order.html', {'order': order, 'found': True})
        except Exception as e:
            return render(request, 'shop/order.html', {'error': 'Order not found or invalid details.', 'found': False})

    return render(request, 'shop/order.html')

# Razorpay configuration
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def checkout(request):
    if request.method == "POST":
        try:
            # Parse JSON data from the frontend
            data = json.loads(request.body)

            # Extract billing details
            billing_details = {
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'country': data.get('country'),
                'address': data.get('address'),
                'city': data.get('city'),
                'postal_code': data.get('postal_code'),
            }

            # Validate fields
            if not all(billing_details.values()):
                return JsonResponse({'error': 'All fields are required!'}, status=400)

            # Retrieve cart items for the logged-in user
            cart_items = Cart.objects.filter(user=request.user)
            if not cart_items.exists():
                return JsonResponse({'error': 'Your cart is empty!'}, status=400)

            # Calculate the total amount (in paise)
            total_price = sum(item.total_cost for item in cart_items) * 100  # Convert to paise

            # Create Razorpay order
            razorpay_order = razorpay_client.order.create({
                'amount': total_price,
                'currency': 'INR',
                'payment_capture': 1  # Auto-capture payment
            })

            # Prepare the response
            response_data = {
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'amount': total_price,
                'billing_details': billing_details,
            }

            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({'error': f'Something went wrong: {str(e)}'}, status=500)

    elif request.method == "GET":
        # Prepare cart items data for GET request (when rendering checkout page)
        cart_items = Cart.objects.filter(user=request.user)
        cart_items_data = [
            {
            'name': item.product.name,
            'sku': item.product.sku,
            'selected_size': item.selected_size,  # Directly accessible
            'total_cost': item.total_cost,       # Directly accessible
        }
        for item in cart_items
    ]

        # Calculate the total price
        total_price = sum(item.total_cost for item in cart_items)

        return render(request, "shop/checkout.html", {
            'cart_items': cart_items_data,
            'total_price': total_price
        })


def order_confirmation(request, order_id):
    try:
        # Fetch the order by its id
        order = Orders.objects.get(id=order_id)
        return render(request, 'shop/order_confirmation.html', {'order': order})
    except Orders.DoesNotExist:
        return render(request, 'shop/order_confirmation.html', {'error': 'Order not found'})


def productssidebar(request, name):
    if Category.objects.filter(name=name, status=0).exists():
        products = Product.objects.filter(Category__name=name)

        grouped_products = {}
        for product in products:
            sku_parts = product.sku.split('-')
            if len(sku_parts) >= 3:
                format_prefix = "-".join(sku_parts[:-2])  # Extract format prefix
                sequence_number = sku_parts[-2]          # Extract sequence number

                # Use format_prefix and sequence_number as the key to group SKUs
                group_key = f"{format_prefix}-{sequence_number}"

                if group_key not in grouped_products:
                    grouped_products[group_key] = {
                        "product": product,  # Store the first product in the group
                        "sizes": []
                    }
                grouped_products[group_key]["sizes"].extend(product.get_all_sizes())

        # Prepare data for the frontend
        grouped_products_data = [
            {
                "product": data["product"],
                "sizes": sorted(set(data["sizes"])),  # Ensure sizes are unique and sorted
            }
            for data in grouped_products.values()
        ]

        return render(
            request,
            "shop/product-sidebar.html",
            {"grouped_products": grouped_products_data, "category_name": name},
        )
    else:
        messages.warning(request, "No Such Category Found")
        return redirect('home')



def productsinfo(request, cname, pname):
    if not cname:
        messages.error(request, "Invalid category name.")
        return redirect("home")

    if Category.objects.filter(name=cname, status=0).exists():
        # Fetch the product based on name or other unique identifiers
        product = Product.objects.filter(name=pname, status=0).first()
        
        if product:
            extracted_size = product.get_size()
            available_sizes = product.get_all_sizes()

            return render(
                request,
                "shop/product-info.html",
                {
                    "products": product,
                    "extracted_size": extracted_size,
                    "available_sizes": available_sizes,
                },
            )
        else:
            messages.warning(request, "No Such Product Found")
            return redirect("productssidebar", name=cname)
    else:
        messages.warning(request, "No Such Category Found")
        return redirect("productssidebar", name=cname)

@csrf_exempt
def payment_verification(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Validate Razorpay signature
            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_signature = data.get('razorpay_signature')

            params = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }

            razorpay_client.utility.verify_payment_signature(params)

            # Save the order
            with transaction.atomic():
                cart_items = Cart.objects.filter(user=request.user)
                total_price = sum(item.total_cost for item in cart_items)

                # Create the order after successful payment
                order = Orders.objects.create(
                    customer=request.user,
                    cart_items=[
                        {
                            'product_sku': item.product.sku,
                            'product_name': item.product.name,
                            'quantity': item.product_qty,
                            'price_per_item': item.product.selling_price,
                            'total_price': item.total_cost,
                        }
                        for item in cart_items
                    ],
                    total_price=total_price,
                    **data.get('billing_details'),
                    status='Paid',
                    razorpay_order_id=razorpay_order_id,
                )

                # Deduct stock
                for item in cart_items:
                    item.product.quantity -= item.product_qty
                    item.product.save()

                # Clear cart
                cart_items.delete()

                print(f"Payment verified successfully. Order ID: {order.id}")

                # Return JSON with redirect URL
            redirect_url = reverse('order_confirmation', kwargs={'order_id': order.id})
            return JsonResponse({'status': 'success', 'redirect_url': redirect_url})
            

        except Exception as e:
            return JsonResponse({'error': f'Payment verification failed: {str(e)}'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)