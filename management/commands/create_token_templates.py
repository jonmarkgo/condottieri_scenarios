from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw
import os

class Command(BaseCommand):
    help = 'Creates token template images'

    def handle(self, *args, **options):
        media_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'media', 'scenarios', 'token_templates')
        os.makedirs(media_dir, exist_ok=True)

        # Create badge base template
        badge_base = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(badge_base)
        draw.ellipse((2, 2, 62, 62), outline='#000000', width=2)
        badge_base.save(os.path.join(media_dir, 'badge-base.png'))

        # Create army base template
        army_base = Image.new('RGBA', (48, 48), (0, 0, 0, 0))
        draw = ImageDraw.Draw(army_base)
        draw.ellipse((2, 2, 46, 46), outline='#000000', width=2)
        army_base.save(os.path.join(media_dir, 'army-base.png'))

        # Create garrison base template
        garrison_base = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        draw = ImageDraw.Draw(garrison_base)
        draw.ellipse((2, 2, 30, 30), outline='#000000', width=2)
        garrison_base.save(os.path.join(media_dir, 'garrison-base.png'))

        # Create fleet base template
        fleet_base = Image.new('RGBA', (48, 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(fleet_base)
        draw.rounded_rectangle((2, 2, 46, 22), radius=7, outline='#000000', width=2)
        fleet_base.save(os.path.join(media_dir, 'fleet-base.png'))

        # Create ship icon template
        ship_icon = Image.new('RGBA', (48, 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(ship_icon)
        # Draw a simple ship shape
        draw.polygon([(4, 12), (12, 8), (16, 12), (32, 8), (32, 4), (16, 8), (12, 4), (4, 8)], fill='#000000')
        draw.line([(4, 4), (4, 20)], fill='#000000', width=2)
        ship_icon.save(os.path.join(media_dir, 'ship-icon.png'))

        self.stdout.write(self.style.SUCCESS('Successfully created token template images')) 