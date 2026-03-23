#api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
from menu.models import Category, MenuItem
from orders.models import Order, OrderItem, Table
from .serializer import (
    CategorySerializer, MenuItemSerializer,
    OrderSerializer, OrderCreateSerializer,
    OrderUpdateSerializer, OrderStatusSerializer,
    OrderItemSerializer, TableSerializer, AddItemsSerializer,
    OpenTableSerializer, PaymentSerializer
)
from .pagination import StandardResultsSetPagination

class TableViewSet(viewsets.ModelViewSet):
    """Manage restaurant tables"""
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['post'])
    def open(self, request, pk=None):
        """Open a table and start a new order"""
        table = self.get_object()
        
        if table.is_occupied:
            return Response(
                {'error': 'Table is already occupied'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = OpenTableSerializer(data=request.data)
        if serializer.is_valid():
            order = table.open_table()
            
            # Update order with customer info if provided
            if serializer.validated_data.get('customer_name'):
                order.customer_name = serializer.validated_data['customer_name']
            if serializer.validated_data.get('customer_phone'):
                order.customer_phone = serializer.validated_data['customer_phone']
            if serializer.validated_data.get('notes'):
                order.notes = serializer.validated_data['notes']
            order.save()
            
            return Response(
                OrderSerializer(order).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close a table (after payment)"""
        table = self.get_object()
        
        if not table.is_occupied:
            return Response(
                {'error': 'Table is not occupied'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if table.current_order and not table.current_order.is_paid:
            return Response(
                {'error': 'Order must be paid before closing table'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        table.close_table()
        
        return Response(
            {'status': 'success', 'message': f'Table {table.number} closed'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def current_order(self, request, pk=None):
        """Get current order for a table"""
        table = self.get_object()
        
        if not table.current_order:
            return Response(
                {'error': 'No active order for this table'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(OrderSerializer(table.current_order).data)
    
    @action(detail=True, methods=['post'])
    def add_items(self, request, pk=None):
        """Add items to the current order of a table"""
        table = self.get_object()
        
        if not table.is_occupied or not table.current_order:
            return Response(
                {'error': 'Table has no active order'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AddItemsSerializer(data=request.data)
        if serializer.is_valid():
            order = table.current_order
            items_data = serializer.validated_data['items']
            
            created_items = []
            for item_data in items_data:
                menu_item = MenuItem.objects.get(id=item_data['menu_item_id'])
                order_item = OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item_data['quantity'],
                    notes=item_data.get('notes', ''),
                    unit_price=menu_item.price
                )
                created_items.append(order_item)
                
                # Send to kitchen immediately
                self._send_to_kitchen(order_item)
            
            order.calculate_total()
            
            return Response({
                'status': 'success',
                'items_added': OrderItemSerializer(created_items, many=True).data,
                'order': OrderSerializer(order).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _send_to_kitchen(self, order_item):
        """Send item to kitchen printer/display"""
        # Implement kitchen notification logic here
        from .utils import print_order_item_to_kitchen
        try:
            print_order_item_to_kitchen(order_item)
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to print to kitchen: {e}")
    
    @action(detail=True, methods=['post'])
    def request_bill(self, request, pk=None):
        """Customer requests the bill"""
        table = self.get_object()
        
        if not table.current_order:
            return Response(
                {'error': 'No active order for this table'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        order = table.current_order
        order.request_payment()
        
        # Generate bill summary
        bill_summary = {
            'order_number': order.order_number,
            'table': table.number,
            'items': OrderItemSerializer(
                order.items.filter(is_cancelled=False),
                many=True
            ).data,
            'total': order.total_amount,
            'created_at': order.created_at,
            'duration': str(timezone.now() - order.created_at)
        }
        
        return Response(bill_summary)
    
    @action(detail=True, methods=['post'])
    def process_payment(self, request, pk=None):
        """Process payment for a table"""
        table = self.get_object()
        
        if not table.current_order:
            return Response(
                {'error': 'No active order for this table'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            order = table.current_order
            payment_method = serializer.validated_data['payment_method']
            
            # Complete payment
            order.complete_payment(payment_method)
            
            # Generate receipt
            receipt = {
                'order_number': order.order_number,
                'table': table.number,
                'total': order.total_amount,
                'payment_method': payment_method,
                'paid_at': order.closed_at,
                'change': 0
            }
            
            # Calculate change if cash payment
            if payment_method == 'cash' and 'amount_received' in serializer.validated_data:
                amount_received = serializer.validated_data['amount_received']
                receipt['amount_received'] = amount_received
                receipt['change'] = amount_received - order.total_amount
            
            return Response(receipt)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for categories"""
    queryset = Category.objects.filter(is_active=True).order_by('order')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None  # No pagination for categories

class MenuItemViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for menu items"""
    queryset = MenuItem.objects.filter(is_available=True)
    serializer_class = MenuItemSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by category
        category_id = self.request.query_params.get('category_id')
        category_slug = self.request.query_params.get('category_slug')
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        elif category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter by special
        is_special = self.request.query_params.get('special')
        if is_special:
            queryset = queryset.filter(is_special=True)
        
        return queryset.order_by('category__order', 'name')
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get menu items grouped by category"""
        categories = Category.objects.filter(
            is_active=True
        ).prefetch_related(
            'items'
        ).order_by('order')
        
        result = []
        for category in categories:
            items = MenuItemSerializer(
                category.items.filter(is_available=True),
                many=True
            ).data
            
            if items:  # Only include categories with available items
                result.append({
                    'category': CategorySerializer(category).data,
                    'items': items
                })
        
        return Response(result)

class OrderViewSet(viewsets.ModelViewSet):
    """Full CRUD viewset for orders"""
    queryset = Order.objects.all()
    permission_classes = [AllowAny]  # In production, add authentication
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        elif self.action == 'update_status':
            return OrderStatusSerializer
        return OrderSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date
        date_filter = self.request.query_params.get('date')
        if date_filter == 'today':
            today = timezone.now().date()
            queryset = queryset.filter(created_at__date=today)
        elif date_filter == 'week':
            week_ago = timezone.now() - timedelta(days=7)
            queryset = queryset.filter(created_at__gte=week_ago)
        
        # Filter by payment status
        is_paid = self.request.query_params.get('is_paid')
        if is_paid is not None:
            queryset = queryset.filter(is_paid=is_paid.lower() == 'true')
        
        # Filter by table
        table = self.request.query_params.get('table')
        if table:
            queryset = queryset.filter(table_number=table)
        
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Return the created order with full details
        output_serializer = OrderSerializer(order)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        serializer = OrderStatusSerializer(data=request.data)
        
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            order.status = new_status
            order.save()
            
            return Response({
                'status': 'success',
                'order': OrderSerializer(order).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def add_items(self, request, pk=None):
        """Add items to an existing order"""
        order = self.get_object()
        items_data = request.data.get('items', [])
        
        if not items_data:
            return Response(
                {'error': 'No items provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        added_items = []
        for item_data in items_data:
            try:
                menu_item = MenuItem.objects.get(
                    id=item_data.get('menu_item_id'),
                    is_available=True
                )
                
                order_item = OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item_data.get('quantity', 1),
                    notes=item_data.get('notes', ''),
                    unit_price=menu_item.price
                )
                added_items.append(order_item)
                
            except MenuItem.DoesNotExist:
                return Response(
                    {'error': f"Menu item {item_data.get('menu_item_id')} not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Recalculate total
        order.calculate_total()
        
        return Response({
            'status': 'success',
            'added_items': OrderItemSerializer(added_items, many=True).data,
            'order': OrderSerializer(order).data
        })
    
    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        """Remove an item from order"""
        order = self.get_object()
        item_id = request.data.get('item_id')
        
        try:
            order_item = order.items.get(id=item_id)
            order_item.delete()
            order.calculate_total()
            
            return Response({
                'status': 'success',
                'order': OrderSerializer(order).data
            })
        except OrderItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in order'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark order as paid"""
        order = self.get_object()
        payment_method = request.data.get('payment_method', 'cash')
        
        order.is_paid = True
        order.payment_method = payment_method
        order.save()
        
        return Response({
            'status': 'success',
            'order': OrderSerializer(order).data
        })
    
    @action(detail=True, methods=['post'])
    def print_order(self, request, pk=None):
        """Print order to kitchen/bar printer"""
        order = self.get_object()
        printer_type = request.data.get('printer', 'kitchen')  # kitchen or bar
        
        from .utils import print_order_to_kitchen
        
        try:
            success = print_order_to_kitchen(order, printer_type)
            if success:
                return Response({
                    'status': 'success',
                    'message': f'Order sent to {printer_type} printer'
                })
            else:
                return Response(
                    {'error': 'Failed to print order'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active orders (not delivered or cancelled)"""
        active_orders = self.get_queryset().exclude(
            status__in=['delivered', 'cancelled']
        )
        
        serializer = self.get_serializer(active_orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def kitchen_queue(self, request):
        """Get orders for kitchen display"""
        orders = self.get_queryset().filter(
            status__in=['confirmed', 'preparing']
        ).order_by('created_at')
        
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get order statistics"""
        today = timezone.now().date()
        
        stats = {
            'today': {
                'count': Order.objects.filter(created_at__date=today).count(),
                'total': Order.objects.filter(
                    created_at__date=today
                ).aggregate(
                    total=Sum('total_amount')
                )['total'] or 0
            },
            'active': Order.objects.exclude(
                status__in=['delivered', 'cancelled']
            ).count(),
            'by_status': {}
        }
        
        # Count by status
        for status_code, status_name in Order.STATUS_CHOICES:
            stats['by_status'][status_code] = Order.objects.filter(
                status=status_code,
                created_at__date=today
            ).count()
        
        return Response(stats)