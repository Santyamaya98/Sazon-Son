from django.core.management.base import BaseCommand
from orders.models import Table

class Command(BaseCommand):
    help = 'Create restaurant tables'
    
    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10)
        parser.add_argument('--prefix', type=str, default='')
    
    def handle(self, *args, **kwargs):
        count = kwargs['count']
        prefix = kwargs['prefix']
        
        for i in range(1, count + 1):
            table_number = f"{prefix}{i}"
            table, created = Table.objects.get_or_create(
                number=table_number,
                defaults={'seats': 4}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created table {table_number}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Table {table_number} already exists')
                )