from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product

@receiver(post_save, sender=Product)
def generate_sku_and_related_products(sender, instance, created, **kwargs):
    if created and not instance.sku:  # Only for new objects without SKU
        sequence_number = 1

        # Check for the last product with the same format_prefix
        last_product = Product.objects.filter(format_prefix=instance.format_prefix).order_by('-created_at').first()
        if last_product and last_product.sku:
            try:
                last_sku_parts = last_product.sku.split('-')
                sequence_number = int(last_sku_parts[-3]) + 1
            except (IndexError, ValueError):
                sequence_number = 1

        # Generate SKU for all sizes
        if instance.sizes:
            size_list = [size.strip() for size in instance.sizes.split(',')]
            for index, size in enumerate(size_list):
                new_sku = f"{instance.format_prefix}-{sequence_number}-{size.upper()}"

                # Ensure the SKU is unique
                if not Product.objects.filter(sku=new_sku).exists():
                    if index == 0:  # Assign the SKU for the primary product
                        instance.sku = new_sku
                        instance.save(update_fields=['sku'])  # Save the SKU for the primary product
                    else:  # Create additional products for other sizes
                        Product.objects.create(
                            sku=new_sku,
                            Category=instance.Category,
                            name=instance.name,
                            vendor=instance.vendor,
                            product_image=instance.product_image,
                            extra_image_1=instance.extra_image_1,
                            extra_image_2=instance.extra_image_2,
                            extra_image_3=instance.extra_image_3,
                            quantity=instance.quantity,
                            original_price=instance.original_price,
                            selling_price=instance.selling_price,
                            description=instance.description,
                            status=instance.status,
                            trending=instance.trending,
                            size_format=instance.size_format,
                            format_prefix=instance.format_prefix,
                            feature_1=instance.feature_1,
                            feature_2=instance.feature_2,
                            feature_3=instance.feature_3,
                            feature_4=instance.feature_4,
                            feature_5=instance.feature_5,
                            feature_6=instance.feature_6,
                            feature_7=instance.feature_7,
                            feature_8=instance.feature_8,
                            feature_9=instance.feature_9,
                            feature_10=instance.feature_10,
                        )
