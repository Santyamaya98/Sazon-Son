#/orders/models.py
from django.db import models

# Create your models here.
from django.db import models
from django.core.validators import MinValueValidator
from django.shortcuts import render
from django.utils import timezone

from decimal import Decimal
from menu.models import MenuItem

def home_view(request):
    # Order tables by number numerically
    all_tables = Table.objects.all().order_by('number')  # ← Add this
    
    context = {
        'all_tables': all_tables,
    }
    return render(request, 'templates/orders.html', context)

class Table(models.Model):
    """Restaurant tables"""
    number = models.CharField(max_length=10, unique=True)
    seats = models.IntegerField(default=4)
    is_occupied = models.BooleanField(default=False)
    current_order = models.OneToOneField(
        'Order', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='active_table'
    )
    
    class Meta:
        ordering = ['number']
    
    def __str__(self):
        return f"Table {self.number} - {'Occupied' if self.is_occupied else 'Available'}"
    
    def open_table(self):
        """Create a new order for this table"""
        if not self.is_occupied:
            order = Order.objects.create(
                table=self,
                status='active'
            )
            self.current_order = order
            self.is_occupied = True
            self.save()
            return order
        return self.current_order
    
    def close_table(self):
        """Close the table and finalize order"""
        if self.current_order:
            self.current_order.status = 'completed'
            self.current_order.save()
        self.is_occupied = False
        self.current_order = None
        self.save()

class Order(models.Model):
    """Main order model"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True)
    table_number = models.CharField(max_length=10, blank=True)
    levar_number = models.CharField(max_length=10, blank=True)
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.status}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            import datetime
            now = datetime.datetime.now()
            self.order_number = f"{now.strftime('%Y%m%d')}{now.strftime('%H%M%S')}"
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        """Calculate total from order items"""
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.save()
        return total

class OrderItem(models.Model):
    """Individual items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.menu_item.price
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"