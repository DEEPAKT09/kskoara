import random
from django.db import models
from django.contrib.auth.models import User
import datetime
import os
from django_jsonfield_backport.models import JSONField
from django.db.models import JSONField 
import uuid
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils.timezone import now

def getFileName(request, filename):
    now_time = datetime.datetime.now().strftime("%Y%m%d%H:%M:%S")
    new_filename="%s%s"%(now_time, filename)
    return os.path.join('uploads/', new_filename)

class CustomerManager(BaseUserManager):
    def create_user(self, email, mobile, address, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not mobile:
            raise ValueError("Mobile number is required")

        email = self.normalize_email(email)
        user = self.model(email=email, mobile=mobile, address=address, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, mobile, address, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, mobile, address, password, **extra_fields)


class Customer(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, default="")
    mobile = models.CharField(max_length=20, unique=True)
    address = models.CharField(max_length=255)
    password = models.CharField(max_length=128, default="defaultpassword")  # Just for migration
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomerManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['mobile', 'address']

    def __str__(self):
        return self.email
    
class Category(models.Model):
    name=models.CharField(max_length=150, null=False, blank=False)
    image=models.ImageField(upload_to=getFileName,null=True, blank=True)
    description=models.TextField(max_length=500, null=False, blank=False)
    status=models.BooleanField(default=False,help_text="0-show, 1-Hidden")
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural ='Categories'
    

class Product(models.Model):
    sku = models.CharField(
        max_length=50,
        primary_key=True,
        unique=True,
        null=False,
        blank=True,  # Allow blank to let the save method populate it
    )
    Category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=150, null=False, blank=False)
    vendor = models.CharField(max_length=150, null=False, blank=False)
    product_image = models.ImageField(upload_to=getFileName, null=True, blank=True)
    extra_image_1 = models.ImageField(upload_to=getFileName, null=True, blank=True)
    extra_image_2 = models.ImageField(upload_to=getFileName, null=True, blank=True)
    extra_image_3 = models.ImageField(upload_to=getFileName, null=True, blank=True)
    quantity = models.IntegerField(null=False, blank=False)
    original_price = models.FloatField(null=False, blank=False)
    selling_price = models.FloatField(null=False, blank=False)
    description = models.TextField(max_length=3500, null=False, blank=False)
    status = models.BooleanField(default=False, help_text="0-show, 1-Hidden")
    trending = models.BooleanField(default=False, help_text="0-default, 1-Trending")
    created_at = models.DateTimeField(auto_now_add=True)

    # Sizes field and format field for SKU generation
    sizes = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Available sizes (e.g., S, M, L, XL, XXL, AGE6)",
    )
    size_format = models.CharField(
        max_length=10,
        choices=[('SIZE', 'SIZE'), ('AGE', 'AGE')],
        null=False,
        blank=False,
        help_text="Specify size format: SIZE (e.g., XL) or AGE (e.g., AGE6)",
    )

    # Format prefix for SKU generation
    format_prefix = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        default="WSHORTS-2COMBO",
        help_text="Enter the format prefix (e.g., WSHORTS-2COMBO)",
    )

    # Fields for features
    feature_1 = models.CharField(max_length=855, null=True, blank=True)
    feature_2 = models.CharField(max_length=855, null=True, blank=True)
    feature_3 = models.CharField(max_length=855, null=True, blank=True)
    feature_4 = models.CharField(max_length=855, null=True, blank=True)
    feature_5 = models.CharField(max_length=855, null=True, blank=True)
    feature_6 = models.CharField(max_length=855, null=True, blank=True)
    feature_7 = models.CharField(max_length=855, null=True, blank=True)
    feature_8 = models.CharField(max_length=855, null=True, blank=True)
    feature_9 = models.CharField(max_length=855, null=True, blank=True)
    feature_10 = models.CharField(max_length=855, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # New product
            sequence_number = 1  # Start sequence number

            # Ensure sizes are provided
            size_list = [size.strip().upper() for size in self.sizes.split(',')] if self.sizes else []
            if not size_list:
                raise ValueError("Sizes field is required for SKU generation.")

            # Find the last sequence number for this format prefix
            last_product = Product.objects.filter(format_prefix=self.format_prefix).order_by('-created_at').first()
            if last_product and last_product.sku:
                try:
                    # Extract the sequence number from the last SKU
                    last_sku_parts = last_product.sku.split('-')
                    sequence_number = int(last_sku_parts[-2]) + 1
                except (IndexError, ValueError):
                    sequence_number = 1  # Default if the SKU format is unexpected

            # Generate SKU for the primary product using the first size
            first_size = size_list[0]
            self.sku = f"{self.format_prefix}-{sequence_number}-{first_size}"

            # Ensure SKU uniqueness (though unlikely with the above logic)
            while Product.objects.filter(sku=self.sku).exists():
                sequence_number += 1
                self.sku = f"{self.format_prefix}-{sequence_number}-{first_size}"

            # Save the primary product
            super().save(*args, **kwargs)

            # Generate products for remaining sizes using the same sequence number
            additional_products = []
            for size in size_list[1:]:  # Skip the first size (already saved)
                new_sku = f"{self.format_prefix}-{sequence_number}-{size}"

                # Add the product to the bulk create list
                additional_products.append(Product(
                    sku=new_sku,
                    Category=self.Category,
                    name=self.name,
                    vendor=self.vendor,
                    product_image=self.product_image,
                    extra_image_1=self.extra_image_1,
                    extra_image_2=self.extra_image_2,
                    extra_image_3=self.extra_image_3,
                    quantity=self.quantity,
                    original_price=self.original_price,
                    selling_price=self.selling_price,
                    description=self.description,
                    status=self.status,
                    trending=self.trending,
                    size_format=self.size_format,
                    format_prefix=self.format_prefix,
                    feature_1=self.feature_1,
                    feature_2=self.feature_2,
                    feature_3=self.feature_3,
                    feature_4=self.feature_4,
                    feature_5=self.feature_5,
                    feature_6=self.feature_6,
                    feature_7=self.feature_7,
                    feature_8=self.feature_8,
                    feature_9=self.feature_9,
                    feature_10=self.feature_10,
                ))

            # Use bulk_create to save additional products
            if additional_products:
                Product.objects.bulk_create(additional_products)
        else:
            # Update existing product
            super().save(*args, **kwargs)
            
    def get_size(self):
        """Returns the primary size or a default message."""
        if self.sizes:
            sizes = [size.strip().upper() for size in self.sizes.split(',')]
            return sizes[0] if sizes else "No size specified"
        return "No size specified"

    def get_all_sizes(self):
        """Returns all available sizes as a list, extracting from the SKUs."""
        # Get the prefix part of the SKU, e.g., "2SET-PLAIN-1"
        sku_prefix = '-'.join(self.sku.split('-')[:-1])
        
        # Fetch all products with the same format prefix
        related_products = Product.objects.filter(sku__startswith=sku_prefix)
        
        # Extract the sizes from the SKUs of the related products
        sizes = set()  # Use a set to avoid duplicates
        for product in related_products:
            # Extract size from SKU (the last part)
            size_part = product.sku.split('-')[-1]  # Get the last part of the SKU
            sizes.add(size_part.upper())  # Add size to the set, converting to uppercase
        
        return sorted(sizes)  # Return a sorted list of unique sizes
    def extract_sku_parts(full_sku):
        # Split the SKU into parts by the '-' delimiter
        parts = full_sku.split('-')
        # Example: 'WSHORTS-2COMBO-1-XXXL' -> ['WSHORTS', '2COMBO', '1', 'XXXL']
        
        # Reconstruct the SKU without the size (last part)
        base_sku = '-'.join(parts[:-1])  # Exclude the size (last part)
        
        return base_sku  # Example: 'WSHORTS-2COMBO-1'


class Orders(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Order Confirmed', 'Order Confirmed'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
    )

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cart_items = JSONField(default=list)  # use cart_items = models.JSONField() instead
    total_price = models.FloatField()
    address = models.TextField(default="unknown")
    first_name = models.CharField(max_length=100, default="unknown")
    last_name = models.CharField(max_length=100, default="unknown")
    email = models.EmailField(default="unknown")
    phone = models.CharField(max_length=15, default="unknown")
    country = models.CharField(max_length=100, default="unknown")
    city = models.CharField(max_length=100, default="unknown")
    postal_code = models.CharField(max_length=20, default="unknown")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)


    def __str__(self):
        return f"Order {self.id} by {self.customer.email}"
    
    class Meta:
        verbose_name_plural ='Orders'

    
    @property
    def calculate_total_price(self):
        return self.product.selling_price * self.quantity

 
class Cart(models.Model):
  user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
  product=models.ForeignKey(Product,on_delete=models.CASCADE)
  product_qty=models.IntegerField(null=False,blank=False)
  selected_size = models.CharField(max_length=100, blank=True, null=True)  # Field to store the size

  def __str__(self):
        return f"{self.product.name} - {self.selected_size} - {self.product_qty}"
 
  @property
  def total_cost(self):
    return self.product_qty*self.product.selling_price

class Favourite(models.Model):
	user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
	product = models.ForeignKey(Product, to_field='sku', on_delete=models.CASCADE)  # Reference SKU
	created_at=models.DateTimeField(auto_now_add=True)