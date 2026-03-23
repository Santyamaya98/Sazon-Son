from django.core.management.base import BaseCommand
from menu.models import Category, MenuItem
from decimal import Decimal

class Command(BaseCommand):
    help = 'Load initial menu data'
    
    def handle(self, *args, **kwargs):
        # Create categories
        categories_data = [
            {'name': 'Arroz al Wok', 'slug': 'arroz-al-wok', 'order': 1},
            {'name': 'Entantes y Raciones', 'slug': 'entantes-raciones', 'order': 2},
            {'name': 'Postres', 'slug': 'postres', 'order': 3},
            {'name': 'Platos Combinados', 'slug': 'platos-combinados', 'order': 4},
            {'name': 'Sushi', 'slug': 'sushi', 'order': 5},
            {'name': 'Para Compartir', 'slug': 'para-compartir', 'order': 6},
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created category: {category.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Category already exists: {category.name}"))
        
        # Create menu items with complete data from your HTML
        menu_items_data = [
            # Arroz al Wok
            {
                'category_slug': 'arroz-al-wok',
                'items': [
                    {'name': 'Arroz al Wok - Pollo', 'price': 12.00, 'description': 'Arroz al wok Salteado con vegetales'},
                    {'name': 'Arroz al Wok - Solomillo de Ternera', 'price': 14.00, 'description': 'Arroz al wok Salteado con vegetales'},
                    {'name': 'Arroz al Wok - Mixto', 'price': 14.00, 'description': 'Arroz al wok Salteado con vegetales'},
                ]
            },
            # Entantes y Raciones
            {
                'category_slug': 'entantes-raciones',
                'items': [
                    {'name': 'Langostinos a la plancha (8 unid)', 'price': 13.00},
                    {'name': 'Zamburiñas a la plancha (8 unid)', 'price': 13.00},
                    {'name': 'Chipirones con Patatas (8 unid)', 'price': 11.00},
                    {'name': 'Hamburguesa pollo con Patatas', 'price': 8.50},
                    {'name': 'Hamburguesa mixta con Patatas', 'price': 8.00},
                    {'name': 'Alas de pollo con Patatas', 'price': 7.00},
                    {'name': 'Alas de pollo marinadas en salsa BBQ con Patatas', 'price': 7.50},
                    {'name': 'Finger de pollo con Patatas', 'price': 7.00},
                    {'name': 'Nuggets de pollo con Patatas', 'price': 6.00},
                    {'name': 'Salchichas con Patatas', 'price': 6.00},
                    {'name': 'Huevos rotos - chorizo y Patatas', 'price': 6.00},
                    {'name': 'Patatas Ail-oli ó Brava', 'price': 4.00},
                ]
            },
            # Postres
            {
                'category_slug': 'postres',
                'items': [
                    {'name': 'Postres Artesanales (Versos)', 'price': 4.50},
                    {'name': 'Mugs Caseros', 'price': 4.00},
                    {'name': 'Tarta Helada con Sirope Chocolate', 'price': 2.50},
                    {'name': 'Queso con Membrillo', 'price': 4.00},
                    {'name': 'Batidos fruta Fresca', 'price': 4.00},
                ]
            },
            # Platos Combinados
            {
                'category_slug': 'platos-combinados',
                'items': [
                    {'name': 'Churrasco de Ternera a la Brasa', 'price': 13.00},
                    {'name': 'Parrillada Mixta', 'price': 14.00, 'description': 'Selección de carnes a la parrilla'},
                    {'name': 'Cachopo de Ternera con Patatas', 'price': 15.00, 'description': 'Filete de ternera empanado relleno'},
                    {'name': 'Filete Ternera', 'price': 9.50, 'description': 'A la plancha - Ensalada Mixta - Patatas fritas'},
                    {'name': 'Costillas de Cerdo', 'price': 9.00},
                    {'name': 'Zorza Gallega de Cerdo', 'price': 8.50},
                    {'name': 'Pechuga de Pollo', 'price': 8.50, 'description': 'A la plancha - Ensalada Mixta - Patatas fritas'},
                    {'name': 'Pechuga de Pollo Gratinada en Salsa', 'price': 9.00},
                    {'name': 'Pechuga de Pollo Marinada en Salsa Teriyaki', 'price': 9.00},
                    {'name': 'Filete de Merluza', 'price': 8.50, 'description': 'A la plancha - Ensalada Mixta - Patatas fritas'},
                    {'name': 'Salchipapa Especial', 'price': 10.00},
                ]
            },
            # Sushi
            {
                'category_slug': 'sushi',
                'items': [
                    {'name': 'Fuji Roll', 'price': 13.00, 'description': '10 Bocados'},
                    {'name': 'Akira', 'price': 13.00, 'description': '10 Bocados'},
                    {'name': 'Samurai', 'price': 13.00, 'description': '10 Bocados'},
                    {'name': 'Tiger Roll Especial', 'price': 13.00, 'description': '10 Bocados - Roll especial con topping'},
                    {'name': 'Ceviche Maki', 'price': 13.00, 'description': '10 Bocados - Maki con ceviche fresco'},
                    {'name': 'Sellado de Salmón', 'price': 13.00, 'description': '10 Bocados - Salmón sellado con topping especial'},
                    {'name': 'Viagra', 'price': 13.00, 'description': '10 Bocados - Roll afrodisiaco especial'},
                    {'name': 'Ojo de Tigre', 'price': 13.00, 'description': '10 Bocados'},
                    {'name': 'Pasión Roll', 'price': 13.00, 'description': '10 Bocados'},
                    {'name': 'Eden Roll', 'price': 13.00, 'description': '10 Bocados'},
                    {'name': 'California Dinamita', 'price': 13.00, 'description': '10 Bocados'},
                    {'name': 'Ebi Master', 'price': 13.00, 'description': '10 Bocados'},
                    {'name': 'Vegano', 'price': 10.00, 'description': '10 Bocados - Opción vegana'},
                ]
            },
            # Para Compartir
            {
                'category_slug': 'para-compartir',
                'items': [
                    {'name': 'Arroz wok y alitas', 'price': 25.00, 'description': 'Ideal para compartir'},
                    {'name': 'Picada', 'price': 30.00, 'description': 'Selección variada para compartir'},
                ]
            },
        ]
        
        # Process menu items
        for cat_items in menu_items_data:
            try:
                category = Category.objects.get(slug=cat_items['category_slug'])
                
                for item_data in cat_items['items']:
                    # Convert price to Decimal
                    price_decimal = Decimal(str(item_data['price']))
                    
                    item, created = MenuItem.objects.get_or_create(
                        name=item_data['name'],
                        category=category,
                        defaults={
                            'price': price_decimal,
                            'description': item_data.get('description', ''),
                            'is_available': True,
                        }
                    )
                    
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f"Created item: {item.name} - {item.price}€")
                        )
                    else:
                        # Update price if item already exists
                        if item.price != price_decimal:
                            item.price = price_decimal
                            item.save()
                            self.stdout.write(
                                self.style.WARNING(f"Updated price for: {item.name} - {item.price}€")
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f"Item already exists: {item.name}")
                            )
                        
            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Category not found: {cat_items['category_slug']}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error creating item: {str(e)}")
                )
        
        # Print summary
        total_categories = Category.objects.count()
        total_items = MenuItem.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nData loaded successfully!"
                f"\nTotal Categories: {total_categories}"
                f"\nTotal Menu Items: {total_items}"
            )
        )