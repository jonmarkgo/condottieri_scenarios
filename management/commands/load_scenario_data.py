from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os
import yaml
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.core.files import File
from condottieri_scenarios.models import Setting, Area, Country, Scenario, Border, Religion, CountryRandomIncome, CityRandomIncome, TradeRoute, Configuration

class Command(BaseCommand):
    help = 'Loads all scenario data from YAML files in the data directory'

    def handle(self, *args, **options):
        # Clear existing data
        Border.objects.all().delete()
        Area.objects.all().delete()
        Country.objects.all().delete()
        Scenario.objects.all().delete()
        Setting.objects.all().delete()
        
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'static', 'machiavelli', 'img')
        
        # Create a superuser if none exists
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write(self.style.SUCCESS('Created superuser admin'))

        # Load settings first
        settings_file = os.path.join(data_dir, '00_settings.yaml')
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings_data = yaml.safe_load(f)
                for item in settings_data:
                    if item['model'] == 'condottieri_scenarios.setting':
                        fields = item['fields']
                        try:
                            setting = Setting()
                            setting.id = item['pk']
                            setting.slug = fields['slug']
                            setting.title_en = fields['title_en']
                            setting.title_es = fields.get('title_es', '')
                            setting.title_ca = fields.get('title_ca', '')
                            setting.title_de = fields.get('title_de', '')
                            setting.description_en = fields['description_en']
                            setting.description_es = fields.get('description_es', '')
                            setting.description_ca = fields.get('description_ca', '')
                            setting.description_de = fields.get('description_de', '')
                            setting.editor = User.objects.first()
                            setting.enabled = fields.get('enabled', True)
                            setting.save()
                            self.stdout.write(self.style.SUCCESS(f'Created setting {setting.title}'))
                        except IntegrityError:
                            self.stdout.write(self.style.WARNING(f'Setting {fields["slug"]} already exists'))
                            continue

        # Load areas
        areas_file = os.path.join(data_dir, '01_areas.yaml')
        if os.path.exists(areas_file):
            with open(areas_file, 'r') as f:
                areas_data = yaml.safe_load(f)
                for item in areas_data:
                    if item['model'] == 'condottieri_scenarios.area':
                        fields = item['fields']
                        try:
                            setting = Setting.objects.get(pk=fields['setting'])
                            area = Area()
                            area.id = item['pk']
                            area.setting = setting
                            area.code = fields['code']
                            area.name_en = fields['name_en']
                            area.name_es = fields.get('name_es', '')
                            area.name_ca = fields.get('name_ca', '')
                            area.name_de = fields.get('name_de', '')
                            area.is_sea = fields.get('is_sea', False)
                            area.is_coast = fields.get('is_coast', False)
                            area.has_city = fields.get('has_city', False)
                            area.is_fortified = fields.get('is_fortified', False)
                            area.has_port = fields.get('has_port', False)
                            area.control_income = fields.get('control_income', 1)
                            area.garrison_income = fields.get('garrison_income', 0)
                            area.mixed = fields.get('mixed', False)
                            area.save()
                            self.stdout.write(self.style.SUCCESS(f'Created area {area.name}'))
                        except IntegrityError:
                            self.stdout.write(self.style.WARNING(f'Area {fields["code"]} already exists'))
                            continue

        # Load borders
        borders_file = os.path.join(data_dir, '01_borders.yaml')
        if os.path.exists(borders_file):
            with open(borders_file, 'r') as f:
                borders_data = yaml.safe_load(f)
                for item in borders_data:
                    if item['model'] == 'condottieri_scenarios.border':
                        fields = item['fields']
                        try:
                            from_area = Area.objects.get(pk=fields['from_area'])
                            to_area = Area.objects.get(pk=fields['to_area'])
                            border = Border()
                            border.id = item['pk']
                            border.from_area = from_area
                            border.to_area = to_area
                            border.save()
                            self.stdout.write(self.style.SUCCESS(f'Created border {from_area.code} - {to_area.code}'))
                        except IntegrityError:
                            self.stdout.write(self.style.WARNING(f'Border {from_area.code} - {to_area.code} already exists'))
                            continue

        # Load countries
        countries_file = os.path.join(data_dir, '04_countries.yaml')
        if os.path.exists(countries_file):
            with open(countries_file, 'r') as f:
                countries_data = yaml.safe_load(f)
                for item in countries_data:
                    if item['model'] == 'condottieri_scenarios.country':
                        fields = item['fields']
                        try:
                            country = Country()
                            country.id = item['pk']
                            country.name_en = fields['name_en']
                            country.name_es = fields.get('name_es', '')
                            country.name_ca = fields.get('name_ca', '')
                            country.name_de = fields.get('name_de', '')
                            country.static_name = fields['static_name']
                            country.editor = User.objects.first()
                            country.enabled = True

                            # Set coat of arms
                            coat_path = os.path.join(static_dir, f"badge-{country.static_name}.png")
                            if os.path.exists(coat_path):
                                with open(coat_path, 'rb') as f:
                                    country.coat_of_arms.save(f"badge-{country.static_name}.png", File(f), save=False)
                            else:
                                self.stdout.write(self.style.WARNING(f"Coat of arms not found for {country.static_name}, using default"))
                                default_coat_path = os.path.join(static_dir, "badge-austria.png")
                                if os.path.exists(default_coat_path):
                                    with open(default_coat_path, 'rb') as f:
                                        country.coat_of_arms.save(f"badge-{country.static_name}.png", File(f), save=False)
                                else:
                                    self.stdout.write(self.style.ERROR(f"Default coat of arms not found at {default_coat_path}"))
                                    continue

                            country.save()
                            self.stdout.write(self.style.SUCCESS(f'Created country {country.name}'))
                        except IntegrityError:
                            self.stdout.write(self.style.WARNING(f'Country {fields["static_name"]} already exists'))
                            continue

        # Load scenarios
        for filename in sorted(os.listdir(data_dir)):
            if filename.startswith('1') and 'scenario' in filename:
                scenario_file = os.path.join(data_dir, filename)
                with open(scenario_file, 'r') as f:
                    scenario_data = yaml.safe_load(f)
                    for item in scenario_data:
                        if item['model'] == 'condottieri_scenarios.scenario':
                            fields = item['fields']
                            try:
                                # Use the first setting if none specified
                                setting_id = fields.get('setting', 1)
                                setting = Setting.objects.get(pk=setting_id)
                                scenario = Scenario()
                                scenario.id = item['pk']
                                scenario.setting = setting
                                scenario.name = fields['name']
                                scenario.title_en = fields['title_en']
                                scenario.title_es = fields.get('title_es', '')
                                scenario.title_ca = fields.get('title_ca', '')
                                scenario.title_de = fields.get('title_de', '')
                                scenario.description_en = fields['description_en']
                                scenario.description_es = fields.get('description_es', '')
                                scenario.description_ca = fields.get('description_ca', '')
                                scenario.description_de = fields.get('description_de', '')
                                scenario.start_year = fields['start_year']
                                scenario.editor = User.objects.first()
                                scenario.enabled = True
                                scenario.save()
                                self.stdout.write(self.style.SUCCESS(f'Created scenario {scenario.title}'))
                            except IntegrityError:
                                self.stdout.write(self.style.WARNING(f'Scenario {fields["name"]} already exists'))
                                continue

        self.stdout.write(self.style.SUCCESS('Successfully loaded all scenario data')) 