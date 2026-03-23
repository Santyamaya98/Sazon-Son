from rest_framework import serializers
from menu.models import Category, MenuItem
from orders.models import Order, OrderItem, Table


class TableSerializer(serializers.ModelSerializer):
    current_order_number = serializers.CharField(
        source='current_order.order_number', 
        read_only=True
    )
    current_order_total = serializers.DecimalField(
        source='current_order.total_amount',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = Table
        fields = [
            'id', 'number', 'seats', 'is_occupied',
            'current_order', 'current_order_number', 'current_order_total'
        ]

class CategorySerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'order', 'is_active', 'items_count']
    
    def get_items_count(self, obj):
        return obj.items.filter(is_available=True).count()

class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'description', 'price', 'image',
            'category', 'category_name', 'category_slug',
            'is_available', 'is_special', 'preparation_time'
        ]

class MenuItemSimpleSerializer(serializers.ModelSerializer):
    """Simplified serializer for nested representations"""
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'price']

class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_details = MenuItemSimpleSerializer(source='menu_item', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'menu_item', 'menu_item_details',
            'quantity', 'unit_price', 'subtotal', 'notes'
        ]
        read_only_fields = ['unit_price', 'subtotal']

class OrderItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'notes']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'table_number', 'customer_name',
            'customer_phone', 'status', 'status_display', 'total_amount',
            'notes', 'created_at', 'updated_at', 'is_paid',
            'payment_method', 'items'
        ]
        read_only_fields = ['order_number', 'total_amount', 'created_at', 'updated_at']

class OrderCreateSerializer(serializers.Serializer):
    table_number = serializers.CharField(max_length=10, required=False, allow_blank=True)
    customer_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    customer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    items = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must have at least one item")
        
        for item in value:
            if 'menu_item_id' not in item or 'quantity' not in item:
                raise serializers.ValidationError(
                    "Each item must have menu_item_id and quantity"
                )
            
            try:
                menu_item = MenuItem.objects.get(
                    id=item['menu_item_id'],
                    is_available=True
                )
            except MenuItem.DoesNotExist:
                raise serializers.ValidationError(
                    f"Menu item with id {item['menu_item_id']} not found or not available"
                )
            
            if item['quantity'] < 1:
                raise serializers.ValidationError("Quantity must be at least 1")
        
        return value
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Create order
        order = Order.objects.create(**validated_data)
        
        # Create order items
        for item_data in items_data:
            menu_item = MenuItem.objects.get(id=item_data['menu_item_id'])
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=item_data['quantity'],
                notes=item_data.get('notes', ''),
                unit_price=menu_item.price
            )
        
        # Calculate total
        order.calculate_total()
        
        return order

class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['table_number', 'customer_name', 'customer_phone', 'notes', 'status']

class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)

class AddItemsSerializer(serializers.Serializer):
    """Serializer for adding items to an existing order"""
    items = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )
    
    def validate_items(self, value):
        for item in value:
            if 'menu_item_id' not in item or 'quantity' not in item:
                raise serializers.ValidationError(
                    "Each item must have menu_item_id and quantity"
                )
            
            try:
                MenuItem.objects.get(id=item['menu_item_id'], is_available=True)
            except MenuItem.DoesNotExist:
                raise serializers.ValidationError(
                    f"Menu item {item['menu_item_id']} not found or not available"
                )
            
            if item['quantity'] < 1:
                raise serializers.ValidationError("Quantity must be at least 1")
        
        return value
    
class OpenTableSerializer(serializers.Serializer):
    """Serializer for opening a table"""
    customer_name = serializers.CharField(required=False, allow_blank=True)
    customer_phone = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

class PaymentSerializer(serializers.Serializer):
    """Serializer for processing payment"""
    payment_method = serializers.ChoiceField(
        choices=['cash', 'card', 'transfer'],
        default='cash'
    )
    amount_received = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )
    