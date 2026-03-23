# orders/admin.py
from django.contrib import admin
from .models import Table, Order, OrderItem

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'seats', 'is_occupied', 'current_order']
    list_filter = ['is_occupied']
    actions = ['close_tables']
    
    def close_tables(self, request, queryset):
        for table in queryset:
            table.close_table()
    close_tables.short_description = "Close selected tables"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'table_number', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'is_paid', 'created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['order_number', 'total_amount']
    search_fields = ['order_number', 'customer_name', 'table_number']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'menu_item', 'quantity', 'unit_price', 'subtotal']
    list_filter = ['order__created_at']
    search_fields = ['order__order_number', 'menu_item__name']
    raw_id_fields = ['order', 'menu_item']