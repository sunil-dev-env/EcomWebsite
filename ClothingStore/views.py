from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q
from .models import Product, Order, OrderItem, Review
from .forms import SignUpForm, UserEditForm, ReviewForm, CheckoutForm
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Product, Category, Order, User, Cart, CartItem
from django.utils.dateparse import parse_date
from django.contrib.auth import update_session_auth_hash


def home(request):
    products = Product.objects.all()
    category = request.GET.get('category', '')
    color = request.GET.get('color', '').lower()
    size = request.GET.get('size', '').upper()
    price = request.GET.get('price','')
    filters_applied = any([category, color, size, price])

    if category:
        products = products.filter(category__name=category)
    if color:
        products = products.filter(color=color)
    if size:
        products = products.filter(size=size)
    if price and price != "Min-Max":
        min_price, max_price = map(int, price.split('-'))
        products = products.filter(price__gte=min_price, price__lte=max_price)

    cart_items = []
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = cart.items.all()

    cart_product_ids = [item.product.id for item in cart_items]

    context = {
        'products': products,
        'cart_product_ids': cart_product_ids,
        'current_category': category,
        'current_color': color,
        'current_size': size,
        'current_price': price if filters_applied else '',
    }

    return render(request, 'home.html', {
        'products': products,
        'cart_product_ids': cart_product_ids,
        'context': context
    })


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def forgot_password(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        dob = request.POST.get('dob')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'Invalid username.')
            return redirect('forgot_password')
        if user.dob == parse_date(dob):
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password reset successfully.')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match.')
                return redirect('forgot_password')
        else:
            messages.error(request, 'Incorrect date of birth.')
            return redirect('forgot_password')
    return render(request, 'forgot_password.html')

def user_login(request):
    error_message = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        print(user)
        if user:
            login(request, user)
            return redirect('home')
        else:
            error_message = 'Invalid username or password.'
    return render(request, 'login.html', {'error_message': error_message})


def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = UserEditForm(instance=request.user)
    return render(request, 'edit_profile.html', {'form': form})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
    total_cost = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_cost': total_cost})

@login_required
def update_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    if request.method == 'POST':
        quantity = request.POST.get('quantity')
        if quantity:
            cart_item.quantity = int(quantity)
            cart_item.save()
    return redirect('cart')

@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')


@login_required
def checkout(request):
    try:
        # Get the user's cart
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)

        # Calculate the total cost
        total_cost = sum(item.product.price * item.quantity for item in cart_items)

        if request.method == 'POST':
            shipping_address = request.POST.get('shipping_address')
            payment_method = request.POST.get('payment_method')

            # Create a new order
            order = Order.objects.create(
                user=request.user,
                shipping_address=shipping_address,
                payment_method=payment_method,
                ordered_date=timezone.now(),
                status='ordered',
                total_cost=total_cost  # Set total cost here
            )

            # Add products to the order
            for item in cart_items:
                order.products.add(item.product)

            # Clear the cart
            cart_items.delete()

            # Redirect to the order placed page
            return redirect('order_placed', order_id=order.id)

        return render(request, 'checkout.html', {'cart_items': cart_items, 'total_cost': total_cost})

    except Cart.DoesNotExist:
        messages.error(request, 'Your cart is empty.')
        return redirect('home')

@login_required
def cancel_it(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status in ['ordered', 'on_the_way']:
        order.status = 'cancelled'
        order.save()
        messages.success(request, "Order has been successfully cancelled.")
    else:
        messages.error(request, "Cannot cancel this order.")
    return redirect('order_history')

@login_required
def request_return(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status in ['cancelled','delivered']:
        order.status = 'return_requested'
        order.save()
        messages.success(request, 'Return requested successfully.')
    return redirect('order_history')

@login_required
def order_placed(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        order = None

    return render(request, 'order_placed.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-ordered_date')
    return render(request, 'order_history.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_detail.html', {'order': order})

def product_search(request):
    query = request.GET.get('q')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    else:
        products = Product.objects.all()
    return render(request, 'product_search.html', {'products': products})


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.order_by('-created_at')
    
    cart_items = []
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = cart.items.all()

    cart_product_ids = [item.product.id for item in cart_items]

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            new_review = form.save(commit=False)
            new_review.product = product
            new_review.user = request.user
            new_review.save()
            return redirect('product_detail', product_id=product_id)
    else:
        form = ReviewForm()
    
    return render(request, 'product_detail.html', {'product': product, 'reviews': reviews, 'cart_product_ids': cart_product_ids, 'form': form})


@staff_member_required
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')


@staff_member_required
def manage_products(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, 'manage_products.html', {'products': products, 'categories': categories})

@require_POST
@staff_member_required
def add_product(request):
    name = request.POST.get('name')
    description = request.POST.get('description')
    image = request.FILES.get('image')
    category_id = request.POST.get('category_id')
    size = request.POST.get('size')
    color = request.POST.get('color')
    price = request.POST.get('price')
    
    if name and description and image and category_id and size and color and price:
        category = get_object_or_404(Category, id=category_id)
        Product.objects.create(name=name, description=description, image=image, category=category, size=size, color=color, price=price)
    return redirect('manage_products')

@require_POST
@staff_member_required
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    name = request.POST.get('name')
    description = request.POST.get('description')
    image = request.FILES.get('image')
    category_id = request.POST.get('category_id')
    size = request.POST.get('size')
    color = request.POST.get('color')
    price = request.POST.get('price')
    
    if name and description and category_id and size and color and price:
        category = get_object_or_404(Category, id=category_id)
        product.name = name
        product.description = description
        if image:
            product.image = image
        product.category = category
        product.size = size
        product.color = color
        product.price = price
        product.save()
    return redirect('manage_products')

@require_POST
@staff_member_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('manage_products')

@staff_member_required
def manage_categories(request):
    categories = Category.objects.all()
    return render(request, 'manage_categories.html', {'categories': categories})

@require_POST
@staff_member_required
def add_category(request):
    category_name = request.POST.get('category_name')
    if category_name:
        Category.objects.create(name=category_name)
    return redirect('manage_categories')

@require_POST
@staff_member_required
def update_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category_name = request.POST.get('category_name')
    if category_name:
        category.name = category_name
        category.save()
    return redirect('manage_categories')

@require_POST
@staff_member_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    return redirect('manage_categories')

@staff_member_required
def manage_orders(request):
    orders = Order.objects.all()
    return render(request, 'manage_orders.html', {'orders': orders})

@require_POST
@staff_member_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    status = request.POST.get('status')
    if status in dict(Order.STATUS_CHOICES).keys():
        order.status = status
        order.save()
    return redirect('manage_orders')

@staff_member_required
def manage_users(request):
    users = User.objects.all()
    return render(request, 'manage_users.html', {'users': users})

@require_POST
@staff_member_required
def promote_to_staff(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_staff = True
    user.save()
    return redirect('manage_users')

@require_POST
@staff_member_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    return redirect('manage_users')

@staff_member_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        order.status = new_status
        order.save()
        messages.success(request, 'Order status updated successfully.')
    return redirect('manage_orders')