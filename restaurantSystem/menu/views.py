from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from orders.models import Table, Order, OrderItem
from api.serializers import TableSerializer, OrderSerializer

# Create your views here.
class TableViewSet(viewsets.ModelViewSet):
    """API endpoint for tables"""
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [AllowAny]
    
    def list(self, request):
        """Override list to return plain array instead of paginated results"""
        tables = Table.objects.all().order_by('number')
        serializer = self.get_serializer(tables, many=True)
        return Response(serializer.data)  # Return array directly, not paginated
    
    @action(detail=True, methods=['post'])
    def open(self, request, pk=None):
        """Open a table and create new order"""
        table = self.get_object()
        
        if table.is_occupied:
            return Response(
                {'error': 'Table is already occupied'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new order for this table
        order = Order.objects.create(
            table=table,
            table_number=table.number,  # Keep backward compatibility
            status='active'
        )
        
        table.current_order = order
        table.is_occupied = True
        table.save()
        
        return Response(OrderSerializer(order).data)
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close a table"""
        table = self.get_object()
        
        if table.current_order:
            table.current_order.status = 'completed'
            table.current_order.save()
        
        table.is_occupied = False
        table.current_order = None
        table.save()
        
        return Response({'status': 'Table closed'})
    
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