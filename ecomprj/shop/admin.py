from django.contrib import admin
from .models import *
from .models import Customer
from django.contrib.auth.admin import UserAdmin
import json
from django.utils.safestring import mark_safe

#class CategoryAdmin(admin.ModelAdmin):
#    list_display=('name','image','description')

@admin.register(Customer)
class CustomerAdmin(UserAdmin):
    model = Customer
    list_display = ('email', 'mobile', 'address', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff')
    search_fields = ('email', 'mobile')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('mobile', 'address')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'mobile', 'address', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

from django.contrib import admin
from .models import Product, Category

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'sku', 
        'quantity', 
        'selling_price', 
        'original_price', 
        'Category', 
        'status', 
        'trending',  
        'created_at'
    )
    list_editable = (
        'quantity', 
        'selling_price', 
        'original_price', 
        'status', 
        'trending'
    )  # Allow inline editing for these fields

    search_fields = ('name', 'sku', 'Category__name')  # Add search functionality
    list_filter = ('Category', 'status', 'trending')  # Add filters for easy navigation

    # Include all fields to allow full editing in the admin form
    fields = (
        'sku',
        'name',
        'Category',
        'vendor',
        'product_image',
        'extra_image_1',
        'extra_image_2',
        'extra_image_3',
        'quantity',
        'original_price',
        'selling_price',
        'description',
        'sizes',
        'size_format',
        'format_prefix',
        'status',
        'trending',
        'feature_1',
        'feature_2',
        'feature_3',
        'feature_4',
        'feature_5',
        'feature_6',
        'feature_7',
        'feature_8',
        'feature_9',
        'feature_10',
    )

    # Optional: Read-only fields
    readonly_fields = ('created_at',)

# Register the Category model
admin.site.register(Category)



@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'total_price', 'status')
    list_editable = ('status',)
    search_fields = ('customer__username', 'id')
    list_filter = ('status', 'created_at', 'country', 'city')

     # Make `formatted_cart_items` read-only and replace `cart_items` in the admin detail view
    readonly_fields = ('formatted_cart_items',)

    def formatted_cart_items(self, obj):
        try:
            cart_items = obj.cart_items  # Use the field directly as a list
            if not isinstance(cart_items, list):
                raise ValueError("Cart items must be a list.")

            # Format the cart items into an HTML list
            formatted_items = "<ul>"
            for item in cart_items:
                formatted_items += f"<li><b>Product Name:</b> {item.get('product_name', 'N/A')}<br>"
                formatted_items += f"<b>Product SKU:</b> {item.get('product_sku', 'N/A')}<br>"
                formatted_items += f"<b>Quantity:</b> {item.get('quantity', 'N/A')}<br>"
                formatted_items += f"<b>Price per Item:</b> {item.get('price_per_item', 'N/A')}<br>"
                formatted_items += f"<b>Total Price:</b> {item.get('total_price', 'N/A')}</li>"
            formatted_items += "</ul>"
            return mark_safe(formatted_items)  # Render HTML in admin
        except Exception as e:
            return f"Error displaying cart items: {e}"

    formatted_cart_items.short_description = "Cart Items"

    def get_fields(self, request, obj=None):
        """
        Define the custom field order to ensure `formatted_cart_items` replaces `cart_items`
        and is displayed as the second field.
        """
        fields = super().get_fields(request, obj)
        if obj:
            # Ensure `formatted_cart_items` is second in the field order
            fields = ['customer', 'formatted_cart_items'] + [field for field in fields if field not in ['cart_items', 'customer', 'formatted_cart_items']]
        return fields