from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os
import yaml
import xml.etree.ElementTree as ET
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.core.files import File
from condottieri_scenarios.models import (
    Setting, Area, Country, Scenario, Border, Religion, 
    CountryRandomIncome, CityRandomIncome, TradeRoute, 
    Configuration, Contender, Treasury, ControlToken, GToken,
    SpecialUnit, FamineCell, PlagueCell, StormCell, RouteStep,
    Home, Setup, CityIncome, DisabledArea, AFToken
)

class Command(BaseCommand):
    help = 'Loads all scenario data from YAML files in the data directory'

    def handle(self, *args, **options):
        try:
            # Clear existing data in its own transaction
            with transaction.atomic():
                self.stdout.write(self.style.WARNING('Clearing existing data...'))
                Border.objects.all().delete()
                Area.objects.all().delete()
                Country.objects.all().delete()
                Scenario.objects.all().delete()
                Setting.objects.all().delete()
                ControlToken.objects.all().delete()
                GToken.objects.all().delete()
                AFToken.objects.all().delete()
                SpecialUnit.objects.all().delete()
                FamineCell.objects.all().delete()
                PlagueCell.objects.all().delete()
                StormCell.objects.all().delete()
                Setup.objects.all().delete()
                Home.objects.all().delete()
                Treasury.objects.all().delete()
                CityIncome.objects.all().delete()
                DisabledArea.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Successfully cleared existing data'))

            # Load data in a separate transaction
            with transaction.atomic():
                self.stdout.write(self.style.WARNING('Loading new data...'))
                self._load_all_data()
                self.stdout.write(self.style.SUCCESS('Successfully loaded all scenario data'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to load data: {str(e)}'))
            # Log the full traceback for debugging
            import traceback
            self.stdout.write(self.style.ERROR(f'Full error: {traceback.format_exc()}'))
            raise

    def _load_all_data(self):
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

                            # Load board image if specified
                            if 'board' in fields:
                                board_path = os.path.join(static_dir, fields['board'])
                                if os.path.exists(board_path):
                                    with open(board_path, 'rb') as f:
                                        setting.board.save(f"board-{fields['slug']}.png", File(f), save=False)
                                        self.stdout.write(self.style.SUCCESS(f'Loaded board image for setting {setting.title}'))
                                else:
                                    self.stdout.write(self.style.WARNING(f'Board image not found at {board_path} for setting {setting.title}'))

                            setting.save()
                            self.stdout.write(self.style.SUCCESS(f'Created setting {setting.title}'))
                        except IntegrityError:
                            self.stdout.write(self.style.WARNING(f'Setting {fields["slug"]} already exists'))
                            continue

        # Load settings from setting files
        for filename in os.listdir(data_dir):
            if filename.startswith('17_') and filename.endswith('.yaml'):
                setting_file = os.path.join(data_dir, filename)
                with open(setting_file, 'r') as f:
                    setting_data = yaml.safe_load(f)
                    for item in setting_data:
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

                                # Load board image if specified
                                if 'board' in fields:
                                    board_path = os.path.join(static_dir, fields['board'])
                                    if os.path.exists(board_path):
                                        with open(board_path, 'rb') as f:
                                            setting.board.save(f"board-{fields['slug']}.png", File(f), save=False)
                                            self.stdout.write(self.style.SUCCESS(f'Loaded board image for setting {setting.title} from {filename}'))
                                    else:
                                        self.stdout.write(self.style.WARNING(f'Board image not found at {board_path} for setting {setting.title} from {filename}'))

                                setting.save()
                                self.stdout.write(self.style.SUCCESS(f'Created setting {setting.title} from {filename}'))
                            except IntegrityError:
                                self.stdout.write(self.style.WARNING(f'Setting {fields["slug"]} already exists from {filename}'))
                                continue
                        elif item['model'] == 'condottieri_scenarios.aftoken':
                            fields = item['fields']
                            try:
                                area = Area.objects.get(pk=fields['area'])
                                aftoken = AFToken()
                                aftoken.id = item['pk']
                                aftoken.area = area
                                aftoken.x = fields['x']
                                aftoken.y = fields['y']
                                aftoken.save()
                                self.stdout.write(self.style.SUCCESS(f'Created AFToken for area {area.name}'))
                            except Area.DoesNotExist:
                                self.stdout.write(self.style.ERROR(f'Area {fields["area"]} not found for AFToken'))
                                continue
                            except IntegrityError:
                                self.stdout.write(self.style.WARNING(f'AFToken for area {fields["area"]} already exists'))
                                continue

        # Load religions first
        religions_file = os.path.join(data_dir, '03_religions.yaml')
        if os.path.exists(religions_file):
            with open(religions_file, 'r') as f:
                religions_data = yaml.safe_load(f)
                for item in religions_data:
                    if item['model'] == 'condottieri_scenarios.religion':
                        fields = item['fields']
                        try:
                            # Create religion with all fields
                            religion = Religion()
                            religion.id = item['pk']
                            religion.slug = fields['slug']
                            religion.name_en = fields['name_en']
                            religion.name_es = fields.get('name_es', '')
                            religion.name_ca = fields.get('name_ca', '')
                            religion.name_de = fields.get('name_de', '')
                            religion.save()
                            self.stdout.write(self.style.SUCCESS(f'Created religion {religion.name_en}'))
                        except IntegrityError:
                            self.stdout.write(self.style.WARNING(f'Religion {fields["slug"]} already exists'))
                            continue
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Error creating religion {fields.get("name_en", "unknown")}: {str(e)}'))
                            continue

        # Load special units before countries
        special_units_file = os.path.join(data_dir, '03_special_units.yaml')
        if os.path.exists(special_units_file):
            with open(special_units_file, 'r') as f:
                special_units_data = yaml.safe_load(f)
                for item in special_units_data:
                    if item['model'] == 'condottieri_scenarios.specialunit':
                        fields = item['fields']
                        try:
                            unit = SpecialUnit()
                            unit.id = item['pk']
                            unit.cost = fields['cost']
                            unit.loyalty = fields['loyalty']
                            unit.power = fields['power']
                            unit.static_title = fields['static_title']
                            unit.title_en = fields['title_en']
                            unit.title_es = fields.get('title_es', '')
                            unit.title_de = fields.get('title_de', '')
                            unit.title_ca = fields.get('title_ca', '')
                            unit.save()
                            self.stdout.write(self.style.SUCCESS(f'Created special unit {unit.static_title}'))
                        except IntegrityError:
                            self.stdout.write(self.style.WARNING(f'Special unit {fields["static_title"]} already exists'))
                            continue

        # Load areas after religions
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

                            # Set religion if specified in fields
                            if 'religion' in fields and fields['religion'] is not None:
                                try:
                                    religion = Religion.objects.get(pk=fields['religion'])
                                    area.religion = religion
                                    self.stdout.write(self.style.SUCCESS(f'Set religion {religion.name_en} for area {area.name_en}'))
                                except Religion.DoesNotExist:
                                    self.stdout.write(self.style.ERROR(f'Religion {fields["religion"]} not found for area {area.name_en}'))
                                    continue
                            else:
                                self.stdout.write(self.style.WARNING(f'No religion specified for area {area.name_en}'))

                            area.save()
                            self.stdout.write(self.style.SUCCESS(f'Created area {area.name}'))
                        except IntegrityError:
                            self.stdout.write(self.style.WARNING(f'Area {fields["code"]} already exists'))
                            continue

        # Load areas from setting files
        for filename in os.listdir(data_dir):
            if filename.startswith('17_') and filename.endswith('.yaml'):
                setting_file = os.path.join(data_dir, filename)
                with open(setting_file, 'r') as f:
                    setting_data = yaml.safe_load(f)
                    for item in setting_data:
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

                                # Set religion if specified in fields
                                if 'religion' in fields and fields['religion'] is not None:
                                    try:
                                        religion = Religion.objects.get(pk=fields['religion'])
                                        area.religion = religion
                                        self.stdout.write(self.style.SUCCESS(f'Set religion {religion.name_en} for area {area.name_en} from {filename}'))
                                    except Religion.DoesNotExist:
                                        self.stdout.write(self.style.ERROR(f'Religion {fields["religion"]} not found for area {area.name_en} in {filename}'))
                                        continue
                                else:
                                    self.stdout.write(self.style.WARNING(f'No religion specified for area {area.name_en} in {filename}'))

                                area.save()
                                self.stdout.write(self.style.SUCCESS(f'Created area {area.name} from {filename}'))
                            except IntegrityError:
                                self.stdout.write(self.style.WARNING(f'Area {fields["code"]} already exists from {filename}'))
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
                            # Start a new transaction for each border
                            with transaction.atomic():
                                # First check if border already exists
                                from_area = Area.objects.get(pk=fields['from_area'])
                                to_area = Area.objects.get(pk=fields['to_area'])
                                
                                if Border.objects.filter(from_area=from_area, to_area=to_area).exists():
                                    self.stdout.write(self.style.WARNING(f'Border {from_area.code} - {to_area.code} already exists'))
                                    continue
                                
                                border = Border()
                                border.id = item['pk']
                                border.from_area = from_area
                                border.to_area = to_area
                                border.only_land = fields.get('only_land', False)
                                border.save()
                                self.stdout.write(self.style.SUCCESS(f'Created border {from_area.code} - {to_area.code}'))
                        except Area.DoesNotExist as e:
                            self.stdout.write(self.style.ERROR(f'Area not found for border: {str(e)}'))
                            continue
                        except IntegrityError as e:
                            self.stdout.write(self.style.WARNING(f'Border creation failed due to integrity error: {str(e)}'))
                            continue
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Unexpected error creating border: {str(e)}'))
                            continue

        # Load countries after special units
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
                            country.can_excommunicate = fields.get('can_excommunicate', False)
                            country.protected = fields.get('protected', False)
                            country.color = fields.get('color', '')

                            # Set religion if specified
                            if 'religion' in fields:
                                try:
                                    religion = Religion.objects.get(pk=fields['religion'])
                                    country.religion = religion
                                    self.stdout.write(self.style.SUCCESS(f'Set religion {religion.name_en} for country {country.name_en}'))
                                except Religion.DoesNotExist:
                                    self.stdout.write(self.style.ERROR(f'Religion {fields["religion"]} not found for country {fields["name_en"]}'))
                                    continue
                            else:
                                self.stdout.write(self.style.WARNING(f'No religion specified for country {fields["name_en"]}'))

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
                            
                            # Set special units if specified
                            if 'special_units' in fields:
                                try:
                                    special_units = SpecialUnit.objects.filter(pk__in=fields['special_units'])
                                    country.special_units.set(special_units)
                                    self.stdout.write(self.style.SUCCESS(f'Set special units for country {country.name_en}'))
                                except SpecialUnit.DoesNotExist as e:
                                    self.stdout.write(self.style.ERROR(f'Special unit not found for country {country.name_en}: {str(e)}'))
                                    continue
                            
                            self.stdout.write(self.style.SUCCESS(f'Created country {country.name}'))
                        except IntegrityError:
                            self.stdout.write(self.style.WARNING(f'Country {fields["static_name"]} already exists'))
                            continue

        # Load random incomes
        random_incomes_file = os.path.join(data_dir, '05_random_incomes.yaml')
        if os.path.exists(random_incomes_file):
            with open(random_incomes_file, 'r') as f:
                random_incomes_data = yaml.safe_load(f)
                for item in random_incomes_data:
                    if item['model'] == 'condottieri_scenarios.countryrandomincome':
                        fields = item['fields']
                        try:
                            country = Country.objects.get(pk=fields['country'])
                            setting = Setting.objects.get(pk=fields['setting'])
                            income = CountryRandomIncome()
                            income.id = item['pk']
                            income.country = country
                            income.setting = setting
                            income.income_list = fields['income_list']
                            income.save()
                            self.stdout.write(self.style.SUCCESS(f'Created country random income for {country.name}'))
                        except Country.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Country {fields["country"]} not found for random income'))
                            continue
                        except Setting.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Setting {fields["setting"]} not found for country random income'))
                            continue
                    elif item['model'] == 'condottieri_scenarios.cityrandomincome':
                        fields = item['fields']
                        try:
                            area = Area.objects.get(pk=fields['city'])
                            income = CityRandomIncome()
                            income.id = item['pk']
                            income.city = area
                            income.income_list = fields['income_list']
                            income.save()
                            self.stdout.write(self.style.SUCCESS(f'Created city random income for {area.name}'))
                        except Area.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Area {fields["city"]} not found for random income'))
                            continue

        # Load trade routes
        trade_routes_file = os.path.join(data_dir, '06_trade_routes.yaml')
        if os.path.exists(trade_routes_file):
            with open(trade_routes_file, 'r') as f:
                trade_routes_data = yaml.safe_load(f)
                for item in trade_routes_data:
                    if item['model'] == 'condottieri_scenarios.traderoute':
                        fields = item['fields']
                        try:
                            trade_route = TradeRoute()
                            trade_route.id = item['pk']
                            trade_route.save()
                            self.stdout.write(self.style.SUCCESS(f'Created trade route {trade_route.id}'))
                        except IntegrityError:
                            self.stdout.write(self.style.WARNING(f'Trade route {item["pk"]} already exists'))
                            continue
                    elif item['model'] == 'condottieri_scenarios.routestep':
                        fields = item['fields']
                        try:
                            route = TradeRoute.objects.get(pk=fields['route'])
                            area = Area.objects.get(pk=fields['area'])
                            step = RouteStep()
                            step.id = item['pk']
                            step.route = route
                            step.area = area
                            step.is_end = fields.get('is_end', False)
                            step.save()
                            self.stdout.write(self.style.SUCCESS(f'Created route step for area {area.code}'))
                        except TradeRoute.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Trade route {fields["route"]} not found for route step'))
                            continue
                        except Area.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Area {fields["area"]} not found for route step'))
                            continue

        # Load route steps from setting files
        for filename in os.listdir(data_dir):
            if filename.startswith('17_') and filename.endswith('.yaml'):
                setting_file = os.path.join(data_dir, filename)
                with open(setting_file, 'r') as f:
                    setting_data = yaml.safe_load(f)
                    for item in setting_data:
                        if item['model'] == 'condottieri_scenarios.routestep':
                            fields = item['fields']
                            try:
                                route = TradeRoute.objects.get(pk=fields['route'])
                                area = Area.objects.get(pk=fields['area'])
                                step = RouteStep()
                                step.id = item['pk']
                                step.route = route
                                step.area = area
                                step.is_end = fields.get('is_end', False)
                                step.save()
                                self.stdout.write(self.style.SUCCESS(f'Created route step for area {area.code} from {filename}'))
                            except TradeRoute.DoesNotExist:
                                self.stdout.write(self.style.WARNING(f'Trade route {fields["route"]} not found for route step in {filename}'))
                                continue
                            except Area.DoesNotExist:
                                self.stdout.write(self.style.WARNING(f'Area {fields["area"]} not found for route step in {filename}'))
                                continue
                            except IntegrityError:
                                self.stdout.write(self.style.WARNING(f'Route step {item["pk"]} already exists from {filename}'))
                                continue

        # Load scenarios and contenders
        for filename in sorted(os.listdir(data_dir)):
            if filename.startswith('1') and 'scenario' in filename:
                scenario_file = os.path.join(data_dir, filename)
                with open(scenario_file, 'r') as f:
                    scenario_data = yaml.safe_load(f)
                    scenario = None
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
                        elif item['model'] == 'condottieri_scenarios.contender':
                            if scenario is None:
                                self.stdout.write(self.style.ERROR(f'Cannot create contender without scenario in {filename}'))
                                continue
                            fields = item['fields']
                            try:
                                # Check if this is an autonomous contender (no country)
                                if fields.get('country') is None:
                                    # Check if an autonomous contender already exists for this scenario
                                    existing_autonomous = Contender.objects.filter(scenario=scenario, country__isnull=True).first()
                                    if existing_autonomous:
                                        self.stdout.write(self.style.WARNING(f'Skipping duplicate autonomous contender for scenario {scenario.title}'))
                                        continue
                                
                                contender = Contender()
                                contender.id = item['pk']
                                contender.scenario = scenario
                                if fields.get('country'):
                                    contender.country = Country.objects.get(pk=fields['country'])
                                contender.save()
                                self.stdout.write(self.style.SUCCESS(f'Created contender {contender.id} for scenario {scenario.title}'))
                            except Country.DoesNotExist:
                                self.stdout.write(self.style.WARNING(f'Country {fields["country"]} not found for contender in scenario {scenario.title}'))
                                continue
                            except IntegrityError:
                                self.stdout.write(self.style.WARNING(f'Contender {item["pk"]} already exists'))
                                continue
                        elif item['model'] == 'condottieri_scenarios.home':
                            fields = item['fields']
                            try:
                                area = Area.objects.get(pk=fields['area'])
                                contender = Contender.objects.get(pk=fields['contender'])
                                home = Home()
                                home.id = item['pk']
                                home.area = area
                                home.contender = contender
                                home.is_home = fields.get('is_home', True)
                                home.save()
                                self.stdout.write(self.style.SUCCESS(f'Created home province for {contender.country.name} in {area.name}'))
                            except Area.DoesNotExist:
                                self.stdout.write(self.style.WARNING(f'Area {fields["area"]} not found for home province'))
                                continue
                            except Contender.DoesNotExist:
                                self.stdout.write(self.style.WARNING(f'Contender {fields["contender"]} not found for home province'))
                                continue
                        elif item['model'] == 'condottieri_scenarios.setup':
                            fields = item['fields']
                            try:
                                self.stdout.write(self.style.SUCCESS(f'Processing setup with fields: {fields}'))
                                
                                # Validate required fields
                                if not all(k in fields for k in ['area', 'contender', 'unit_type']):
                                    error_msg = f'Missing required fields for setup: {fields}'
                                    self.stdout.write(self.style.ERROR(error_msg))
                                    continue
                                
                                # Get related objects
                                try:
                                    area = Area.objects.get(pk=fields['area'])
                                    contender = Contender.objects.get(pk=fields['contender'])
                                except (Area.DoesNotExist, Contender.DoesNotExist) as e:
                                    self.stdout.write(self.style.ERROR(f'Related object not found: {str(e)}'))
                                    continue
                                
                                # Validate unit_type
                                unit_type = fields['unit_type']
                                if unit_type not in ['A', 'F', 'G']:
                                    self.stdout.write(self.style.ERROR(f'Invalid unit_type {unit_type} for setup in {area.name}'))
                                    continue
                                
                                # Create setup in its own transaction
                                with transaction.atomic():
                                    try:
                                        # First check if setup already exists
                                        existing = Setup.objects.filter(
                                            id=item['pk']
                                        ).first()
                                        
                                        if existing:
                                            self.stdout.write(self.style.WARNING(f'Setup {item["pk"]} already exists, skipping'))
                                            continue
                                            
                                        setup = Setup.objects.create(
                                            id=item['pk'],
                                            area=area,
                                            contender=contender,
                                            unit_type=unit_type
                                        )
                                        country_name = contender.country.name if contender.country else f"Contender {contender.id}"
                                        self.stdout.write(self.style.SUCCESS(f'Created initial setup for {country_name} in {area.name} with unit_type {unit_type}'))
                                    except IntegrityError as e:
                                        self.stdout.write(self.style.WARNING(f'Setup already exists for area {area.name} and contender {contender.id}: {str(e)}'))
                                        continue
                                    except Exception as e:
                                        self.stdout.write(self.style.ERROR(f'Error creating setup: {str(e)}'))
                                        continue
                                    
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f'Error processing setup: {str(e)}'))
                                continue
                        elif item['model'] == 'condottieri_scenarios.treasury':
                            fields = item['fields']
                            try:
                                contender = Contender.objects.get(pk=fields['contender'])
                                treasury = Treasury()
                                treasury.id = item['pk']
                                treasury.contender = contender
                                treasury.ducats = fields['ducats']
                                treasury.double = fields.get('double', False)
                                treasury.save()
                                self.stdout.write(self.style.SUCCESS(f'Created treasury for {contender.country.name} with {treasury.ducats} ducats'))
                            except Contender.DoesNotExist:
                                self.stdout.write(self.style.WARNING(f'Contender {fields["contender"]} not found for treasury'))
                                continue
                        elif item['model'] == 'condottieri_scenarios.cityincome':
                            fields = item['fields']
                            try:
                                city = Area.objects.get(pk=fields['city'])
                                city_income = CityIncome()
                                city_income.id = item['pk']
                                city_income.city = city
                                city_income.scenario = scenario
                                city_income.save()
                                self.stdout.write(self.style.SUCCESS(f'Created city income for {city.name} in scenario {scenario.title}'))
                            except Area.DoesNotExist:
                                self.stdout.write(self.style.WARNING(f'City {fields["city"]} not found for city income'))
                                continue
                        elif item['model'] == 'condottieri_scenarios.disabledarea':
                            fields = item['fields']
                            try:
                                area = Area.objects.get(pk=fields['area'])
                                disabled_area = DisabledArea()
                                disabled_area.id = item['pk']
                                disabled_area.area = area
                                disabled_area.scenario = scenario
                                try:
                                    disabled_area.save()
                                    self.stdout.write(self.style.SUCCESS(f'Created disabled area {area.name} in scenario {scenario.title}'))
                                except IntegrityError:
                                    # If the disabled area already exists, try to update it
                                    existing = DisabledArea.objects.get(scenario=scenario, area=area)
                                    existing.id = item['pk']  # Update the ID if needed
                                    existing.save()
                                    self.stdout.write(self.style.WARNING(f'Updated existing disabled area {area.name} in scenario {scenario.title}'))
                            except Area.DoesNotExist:
                                self.stdout.write(self.style.WARNING(f'Area {fields["area"]} not found for disabled area'))
                                continue

        # Load tokens
        tokens_file = os.path.join(data_dir, '02_tokens.yaml')
        if os.path.exists(tokens_file):
            with open(tokens_file, 'r') as f:
                tokens_data = yaml.safe_load(f)
                for item in tokens_data:
                    if item['model'] == 'condottieri_scenarios.controltoken':
                        fields = item['fields']
                        try:
                            area = Area.objects.get(pk=fields['area'])
                            token = ControlToken()
                            token.id = item['pk']
                            token.area = area
                            token.x = fields['x']
                            token.y = fields['y']
                            token.save()
                            self.stdout.write(self.style.SUCCESS(f'Created control token for area {area.code}'))
                        except Area.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Area {fields["area"]} not found for control token'))
                            continue
                    elif item['model'] == 'condottieri_scenarios.gtoken':
                        fields = item['fields']
                        try:
                            area = Area.objects.get(pk=fields['area'])
                            token = GToken()
                            token.id = item['pk']
                            token.area = area
                            token.x = fields['x']
                            token.y = fields['y']
                            token.save()
                            self.stdout.write(self.style.SUCCESS(f'Created G token for area {area.code}'))
                        except Area.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Area {fields["area"]} not found for G token'))
                            continue
                    elif item['model'] == 'condottieri_scenarios.aftoken':
                        fields = item['fields']
                        try:
                            area = Area.objects.get(pk=fields['area'])
                            token = AFToken()
                            token.id = item['pk']
                            token.area = area
                            token.x = fields['x']
                            token.y = fields['y']
                            token.save()
                            self.stdout.write(self.style.SUCCESS(f'Created AF token for area {area.code}'))
                        except Area.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Area {fields["area"]} not found for AF token'))
                            continue

        # Load natural disasters
        disasters_file = os.path.join(data_dir, '06_natural_disasters.yaml')
        if os.path.exists(disasters_file):
            with open(disasters_file, 'r') as f:
                disasters_data = yaml.safe_load(f)
                for item in disasters_data:
                    if item['model'] == 'condottieri_scenarios.faminecell':
                        fields = item['fields']
                        try:
                            area = Area.objects.get(pk=fields['area'])
                            cell = FamineCell()
                            cell.id = item['pk']
                            cell.area = area
                            cell.column = fields['column']
                            cell.row = fields['row']
                            cell.save()
                            self.stdout.write(self.style.SUCCESS(f'Created famine cell for area {area.code}'))
                        except Area.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Area {fields["area"]} not found for famine cell'))
                            continue
                    elif item['model'] == 'condottieri_scenarios.plaguecell':
                        fields = item['fields']
                        try:
                            area = Area.objects.get(pk=fields['area'])
                            cell = PlagueCell()
                            cell.id = item['pk']
                            cell.area = area
                            cell.column = fields['column']
                            cell.row = fields['row']
                            cell.save()
                            self.stdout.write(self.style.SUCCESS(f'Created plague cell for area {area.code}'))
                        except Area.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Area {fields["area"]} not found for plague cell'))
                            continue
                    elif item['model'] == 'condottieri_scenarios.stormcell':
                        fields = item['fields']
                        try:
                            area = Area.objects.get(pk=fields['area'])
                            cell = StormCell()
                            cell.id = item['pk']
                            cell.area = area
                            cell.column = fields['column']
                            cell.row = fields['row']
                            cell.save()
                            self.stdout.write(self.style.SUCCESS(f'Created storm cell for area {area.code}'))
                        except Area.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Area {fields["area"]} not found for storm cell'))
                            continue

        # Load storm cells from setting files
        for filename in os.listdir(data_dir):
            if filename.startswith('17_') and filename.endswith('.yaml'):
                setting_file = os.path.join(data_dir, filename)
                with open(setting_file, 'r') as f:
                    setting_data = yaml.safe_load(f)
                    for item in setting_data:
                        if item['model'] == 'condottieri_scenarios.stormcell':
                            fields = item['fields']
                            try:
                                area = Area.objects.get(pk=fields['area'])
                                cell = StormCell()
                                cell.id = item['pk']
                                cell.area = area
                                cell.column = fields['column']
                                cell.row = fields['row']
                                cell.save()
                                self.stdout.write(self.style.SUCCESS(f'Created storm cell for area {area.code}'))
                            except Area.DoesNotExist:
                                self.stdout.write(self.style.WARNING(f'Area {fields["area"]} not found for storm cell'))
                                continue

        # Load XML settings
        for filename in os.listdir(data_dir):
            if filename.endswith('.xml'):
                xml_file = os.path.join(data_dir, filename)
                try:
                    tree = ET.parse(xml_file)
                    root = tree.getroot()
                    for item in root.findall(".//object[@model='condottieri_scenarios.stormcell']"):
                        try:
                            area_id = None
                            column = None
                            row = None
                            for field in item.findall('field'):
                                if field.get('name') == 'area':
                                    area_id = field.text
                                elif field.get('name') == 'column':
                                    column = field.text
                                elif field.get('name') == 'row':
                                    row = field.text
                            
                            if area_id and column and row:
                                area = Area.objects.get(pk=area_id)
                                cell = StormCell()
                                cell.id = item.get('pk')
                                cell.area = area
                                cell.column = column
                                cell.row = row
                                cell.save()
                                self.stdout.write(self.style.SUCCESS(f'Created storm cell for area {area.code}'))
                            else:
                                self.stdout.write(self.style.WARNING(f'Missing required fields for storm cell'))
                        except Area.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Area {area_id} not found for storm cell'))
                            continue
                except ET.ParseError as e:
                    self.stdout.write(self.style.ERROR(f'Error parsing XML file {filename}: {str(e)}')) 