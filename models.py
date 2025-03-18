## Copyright (c) 2012 by Jose Antonio Martin <jantonio.martin AT gmail DOT com>
## This program is free software: you can redistribute it and/or modify it
## under the terms of the GNU Affero General Public License as published by the
## Free Software Foundation, either version 3 of the License, or (at your option
## any later version.
##
## This program is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
## FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
## for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.
##
## This license is also included in the file COPYING
##
## AUTHOR: Jose Antonio Martin <jantonio.martin AT gmail DOT com>

import os.path

from django.db import models
from django.db.models import Q
from condottieri_common.translation_compat import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.validators import RegexValidator
from django.forms import ValidationError
from django.conf import settings
from django.urls import reverse

from transmeta import TransMeta

import logging
logger = logging.getLogger(__name__)

import condottieri_scenarios.managers as managers
import condottieri_scenarios.graphics as graphics
import machiavelli.slugify as slugify

class Error(Exception):
    pass

class AreaNotAllowed(Error):
    pass

class HomeIsAutonomous(Error):
    pass

class HomeIsTaken(Error):
    pass

class AreaIsOccupied(Error):
    pass

class WrongUnitType(Error):
    pass

def get_board_upload_path(instance, filename):
    return os.path.join(settings.SCENARIOS_ROOT, "boards", instance.map_name)

class Setting(models.Model, metaclass=TransMeta):
    """ A Setting represents a historic or fictional setting with a map.
    For example, Machiavelli would be a Setting, and Diplomacy could be another Setting. """

    slug = models.SlugField(_("slug"), max_length=50, unique=True)
    title = models.CharField(max_length=128, verbose_name=_("title"), help_text=_("max. 128 characters"))
    description = models.TextField(verbose_name=_("description"))
    editor = models.ForeignKey(User, verbose_name=_("editor"), on_delete=models.CASCADE)
    enabled = models.BooleanField(_("enabled"), default=False)
    board = models.ImageField(_("board"), upload_to=get_board_upload_path)
    permissions = models.ManyToManyField(User, blank=True, related_name="allowed_users", verbose_name=_("permissions"))

    class Meta:
        verbose_name = _("setting")
        verbose_name_plural = _("settings")
        ordering = ["slug",]
        translate = ('title', 'description',)
    
    def save(self, *args, **kwargs):
        if not self.pk:
            slugify.unique_slugify(self, self.title_en, slug_field_name='slug')
        super(Setting, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.title)

    def user_allowed(self, user):
        if user.is_staff:
            return True
        return user in self.permissions.all()

    def _get_map_name(self):
        return "board-%s.png" % self.slug

    map_name = property(_get_map_name)

    def _get_in_play(self):
        for s in self.scenario_set.all():
            if s.in_play:
                return True
        return False
    
    in_play = property(_get_in_play)

class Configuration(models.Model):
    """ Defines the configuration options for each setting. This options are defined when
    the setting is created and are not meant to be changed.
    """

    setting = models.OneToOneField(Setting, verbose_name=_('setting'), editable=False, on_delete=models.CASCADE)
    religious_war = models.BooleanField(_('religious war'), default=False)
    trade_routes = models.BooleanField(_('trade routes'), default=False)

    def __str__(self):
        return str(self.setting)

def create_configuration(sender, instance, created, raw, **kwargs):
    if isinstance(instance, Setting) and created and not raw:
        config = Configuration(setting=instance)
        config.save()

models.signals.post_save.connect(create_configuration, sender=Setting)

class Scenario(models.Model, metaclass=TransMeta):
    """ This class defines a Condottieri scenario. """
    
    setting = models.ForeignKey(Setting, verbose_name=_("setting"), on_delete=models.CASCADE)
    name = models.SlugField(_("slug"), max_length=128, unique=True)
    title = models.CharField(max_length=128, verbose_name=_("title"), help_text=_("max. 128 characters"))
    description = models.TextField(verbose_name=_("description"))
    designer = models.CharField(_("designer"), max_length=30, blank=True, null=True, help_text=_("leave it blank if you are the designer"))
    start_year = models.PositiveIntegerField(_("start year"))
    #number_of_players = models.PositiveIntegerField(_("number of players"), default=0)
    editor = models.ForeignKey(User, verbose_name=_("editor"), on_delete=models.CASCADE)
    enabled = models.BooleanField(_("enabled"), default=False)
    countries = models.ManyToManyField('Country', through='Contender')
    published = models.DateField("publication date", null=True, blank=True)

    class Meta:
        verbose_name = _("scenario")
        verbose_name_plural = _("scenarios")
        ordering = ["setting", "start_year",]
        translate = ('title', 'description',)

    def save(self, *args, **kwargs):
        if not self.name:
            slugify.unique_slugify(self, self.title_en, slug_field_name='name')
        super(Scenario, self).save(*args, **kwargs)

    def _get_number_of_players(self):
        return self.countries.count()

    number_of_players = property(_get_number_of_players)

    def get_max_players(self):
        return self.number_of_players

    def __str__(self):
        return str(self.title)
    
    def get_absolute_url(self):
        return reverse('scenario_detail', args=[self.name,])

    def _get_map_name(self):
        return "scenario-%s.jpg" % self.name

    map_name = property(_get_map_name)
    
    def _get_map_path(self):
        return os.path.join(settings.MEDIA_ROOT, settings.SCENARIOS_ROOT,
            self.map_name)

    map_path = property(_get_map_path)

    def _get_map_url(self):
        return os.path.join(settings.MEDIA_URL, settings.SCENARIOS_ROOT,
            self.map_name)

    map_url = property(_get_map_url)

    def _get_thumbnail_path(self):
        return os.path.join(settings.MEDIA_ROOT, settings.SCENARIOS_ROOT,
            "thumbnails", self.map_name)

    thumbnail_path = property(_get_thumbnail_path)

    def _get_thumbnail_url(self):
        return os.path.join(settings.MEDIA_URL, settings.SCENARIOS_ROOT,
            "thumbnails", self.map_name)
    
    thumbnail_url = property(_get_thumbnail_url)
    
    def _get_in_use(self):
        return self.game_set.count() > 0

    in_use = property(_get_in_use)

    def _get_in_play(self):
        return self.game_set.filter(finished__isnull=True).count() > 0

    in_play = property(_get_in_play)

    #def _get_countries(self):
    #   return Country.objects.filter(home__scenario=self).distinct()
    #
    #countries = property(_get_countries)

    def _get_setup_dict(self):
        """ Returns a dictionary with all the setup data for the scenario."""
        _setup_dict = {}
        for c in self.countries:
            treasury = c.treasury_set.get(scenario=self)
            c_dict = {
                'name': c.name,
                'homes': c.home_set.select_related().filter(scenario=self),
                'setups': c.setup_set.select_related().filter(scenario=self),
                'ducats': treasury.ducats,      
                'double': treasury.double,}
            _setup_dict.update({c.static_name: c_dict})
        return _setup_dict

    setup_dict = property(_get_setup_dict)

    def _get_autonomous(self):
        return Setup.objects.filter(contender__scenario=self, contender__country__isnull=True)

    autonomous = property(_get_autonomous)

    def _get_major_cities(self):
        return self.cityincome_set.all()

    major_cities = property(_get_major_cities)

    def _get_disabled_list(self):
        return Area.objects.filter(disabledarea__scenario=self).values_list('name', flat=True)

    disabled_list = property(_get_disabled_list)

    def _get_times_played(self):
        return self.game_set.filter(finished__isnull=False).count()

    times_played = property(_get_times_played)

    def _get_country_stats(self):
        return Country.objects.scenario_stats(self)
    
    country_stats = property(_get_country_stats)

def create_autonomous(sender, instance, created, raw, **kwargs):
    if isinstance(instance, Scenario) and created and not raw:
        autonomous = Contender(scenario=instance)
        autonomous.save()

models.signals.post_save.connect(create_autonomous, sender=Scenario)

class SpecialUnit(models.Model, metaclass=TransMeta):
    """ A SpecialUnit describes the attributes of a unit that costs more ducats
    than usual and can be more powerful or more loyal """
    static_title = models.CharField(_("static title"), max_length=50)
    title = models.CharField(_("title"), max_length=50)
    cost = models.PositiveIntegerField(_("cost"))
    power = models.PositiveIntegerField(_("power"))
    loyalty = models.PositiveIntegerField(_("loyalty"))

    class Meta:
        verbose_name = _("special unit")
        verbose_name_plural = _("special units")
        translate = ("title",)

    def __str__(self):
        return _("%(title)s (%(cost)sd)") % {'title': self.title,
                                            'cost': self.cost}

    def describe(self):
        return _("Costs %(cost)s; Strength %(power)s; Loyalty %(loyalty)s") % {
            'cost': self.cost,
            'power': self.power,
            'loyalty': self.loyalty}

class Religion(models.Model, metaclass=TransMeta):
    slug = models.SlugField(_("slug"), max_length=20, unique=True)
    name = models.CharField(_("name"), max_length=50)

    class Meta:
        verbose_name = _("religion")
        verbose_name_plural = _("religions")
        translate = ("name",)

    def __str__(self):
        return str(self.name)

def get_coat_upload_path(instance, filename):
    return "scenarios/coats/coat-%s.png" % instance.static_name

class Country(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=50)
    color = models.CharField(_("color"), max_length=6, help_text=_("Hexadecimal RGB color (e.g: FF0000 for pure red)"))
    coat_of_arms = models.ImageField(_("coat of arms"), upload_to=get_coat_upload_path,
        help_text=_("Please, use only 40x40px PNG images with transparency"))
    can_excommunicate = models.BooleanField(_("can excommunicate"), default=False)
    static_name = models.SlugField(_("static name"), max_length=20, unique=True)
    special_units = models.ManyToManyField(SpecialUnit, verbose_name=_("special units"))
    religion = models.ForeignKey(Religion, blank=True, null=True, verbose_name=_("religion"), on_delete=models.CASCADE)
    editor = models.ForeignKey(User, verbose_name=_("editor"), on_delete=models.CASCADE)
    enabled = models.BooleanField(_("enabled"), default=False)
    protected = models.BooleanField(_("protected"), default=False)
    
    objects = managers.CountryManager()

    class Meta:
        verbose_name = _("country")
        verbose_name_plural = _("countries")
        ordering = ["static_name", ]
        translate = ("name",)

    def save(self, *args, **kwargs):
        if not self.pk:
            slugify.unique_slugify(self, self.name_en, slug_field_name='static_name')
        super(Country, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse('country_detail', kwargs={'slug': self.static_name})
    
    def get_income(self, setting):
        try:
            income = self.countryrandomincome_set.get(setting=setting)
        except ObjectDoesNotExist:
            return False
        else:
            return income
    
    def get_random_income(self, setting, die, double):
        income = self.get_income(setting)
        if income:
            return income.get_ducats(die, double=double)
        else:
            logger.error("Random income not found for country %s" % self)
            return 0
            
    def _get_in_play(self):
        return self.contender_set.exclude(scenario__game__finished__isnull=True).count() > 0

    in_play = property(_get_in_play)

models.signals.post_save.connect(graphics.signal_handler_make_country_tokens, sender=Country)

class Contender(models.Model):
    """ A Contender object defines a relationship between an Scenario and a
    Country. """

    country = models.ForeignKey(Country, blank=True, null=True, verbose_name=_("country"), on_delete=models.CASCADE)
    scenario = models.ForeignKey(Scenario, verbose_name=_("scenario"), on_delete=models.CASCADE)
    priority = models.PositiveIntegerField(_("priority"), default=0)

    class Meta:
        verbose_name = _("contender")
        verbose_name_plural = _("contenders")
        unique_together = (("country", "scenario"),)
        ordering = ["scenario__id", "country"]

    def __str__(self):
        if self.country:
            return self.country.name
        else:
            return str(_("Autonomous"))

    def _get_editor(self):
        return self.scenario.editor

    editor = property(_get_editor)

class Treasury(models.Model):
    """
    This class represents the initial amount of ducats that a Country starts
    each Scenario with
    """
    #scenario = models.ForeignKey(Scenario, verbose_name=_("scenario"))
    #country = models.ForeignKey(Country, verbose_name=_("country"))
    contender = models.OneToOneField(Contender, verbose_name=_("contender"), on_delete=models.CASCADE)
    ducats = models.PositiveIntegerField(_("ducats"), default=0)
    double = models.BooleanField(_("double income"), default=False)

    def __str__(self):
        return "%s starts with %s ducats" % (self.contender, self.ducats)

    class Meta:
        verbose_name = _("treasury")
        verbose_name_plural = _("treasuries")
        #unique_together = (("scenario", "country"),)

    def _get_editor(self):
        return self.contender.scenario.editor

    editor = property(_get_editor)

class Area(models.Model, metaclass=TransMeta):
    """ This class describes **only** the area features in the board. The game is
    actually played in GameArea objects.
    """

    setting = models.ForeignKey(Setting, verbose_name=_("setting"), on_delete=models.CASCADE)
    name = models.CharField(max_length=25, verbose_name=_("name"))
    code = models.CharField(_("code"), max_length=5,
        help_text=str(_("1-5 uppercase characters to identify the area")))
    is_sea = models.BooleanField(_("is sea"), default=False,
        help_text=str(_("if checked, the area is a sea, and cannot be controlled")))
    is_coast = models.BooleanField(_("is coast"), default=False)
    has_city = models.BooleanField(_("has city"), default=False)
    is_fortified = models.BooleanField(_("is fortified"), default=False,
        help_text=str(_("check only if the area has a city and is fortified")))
    has_port = models.BooleanField(_("has port"), default=False,
        help_text=str(_("check only if the area has a city and a port")))
    borders = models.ManyToManyField("self", symmetrical=False, through='Border', verbose_name=_("borders"))
    ## control_income is the number of ducats that the area gives to the player
    ## that controls it, including the city (seas give 0)
    control_income = models.PositiveIntegerField(_("control income"),
        null=False, default=0,
        help_text=str(_("the money that a country gets for controlling both the province and the city")))    
    ## garrison_income is the number of ducats given by an unbesieged
    ## garrison in the area's city, if any (no fortified city, 0)
    garrison_income = models.PositiveIntegerField(_("garrison income"),
        null=False, default=0,
        help_text=str(_("the money that a country gets if it has a garrison, but does not control the province")))
    religion = models.ForeignKey(Religion, blank=True, null=True, verbose_name=_("religion"),
        on_delete=models.CASCADE,
        help_text=str(_("used only in settings with the rule of religious wars")))
    ## mixed is true if the area is like Venice
    mixed = models.BooleanField(default=False,
        help_text=str(_("the province is a sea that can be controlled, and cannot hold an army")))

    objects = managers.AreaManager()

    def is_adjacent(self, area, fleet=False):
        """ Two areas can be adjacent through land, but not through a coast."""
        
        if fleet:
            borders = Border.objects.filter(Q(from_area=self, to_area=area)|
                                        Q(from_area=area, to_area=self))
            for b in borders:
                if b.only_land:
                    return False
        return area in self.borders.all()

    def build_possible(self, type):
        """ Returns True if the given type of Unit can be built in the Area. """

        assert type in ('A', 'F', 'G'), 'Wrong unit type'
        if type=='A':
            if self.is_sea or self.mixed == True:
                return False
        elif type=='F':
            if not self.has_port:
                return False
        else:
            if not self.is_fortified:
                return False
        return True
    
    def accepts_type(self, type):
        """ Returns True if the given type of unit can stay in the Area. """
        assert type in ('A','F','G'), 'Wrong unit type'
        if type=='A':
            if self.is_sea or self.mixed == True:
                return False
        elif type=='F':
            if not self.is_sea and not self.is_coast:
                return False
        else:
            if not self.is_fortified:
                return False
        return True

    def __str__(self):
        return str(self.name)
    
    def get_random_income(self, die):
        try:
            income = self.cityrandomincome
        except ObjectDoesNotExist:
            logger.error("Random income not found for city %s" % self)
            return 0
        else:
            return income.get_ducats(die)
            
    class Meta:
        verbose_name = _("area")
        verbose_name_plural = _("areas")
        unique_together = [('setting', 'code'),]
        ordering = ('setting', 'code',)
        translate = ('name', )

class Border(models.Model):
    from_area = models.ForeignKey(Area, related_name="from_borders", on_delete=models.CASCADE)
    to_area = models.ForeignKey(Area, related_name="to_borders", on_delete=models.CASCADE)
    only_land = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("border")
        verbose_name_plural = _("borders")
        unique_together = [('from_area', 'to_area'),]
    
    def __str__(self):
        return "%s - %s" % (self.from_area, self.to_area)

def symmetric_border(sender, instance, created, raw, **kwargs):
    if isinstance(instance, Border) and created and not raw:
        obj, created = Border.objects.get_or_create(from_area=instance.to_area,
            to_area=instance.from_area,
            only_land=instance.only_land)

models.signals.post_save.connect(symmetric_border, sender=Border)

class DisabledArea(models.Model):
    """ A DisabledArea is an Area that is not used in a given Scenario. """
    scenario = models.ForeignKey(Scenario, verbose_name=_("scenario"), on_delete=models.CASCADE)
    area = models.ForeignKey(Area, verbose_name=_("area"), on_delete=models.CASCADE)

    def __str__(self):
        return "%(area)s disabled in %(scenario)s" % {'area': self.area,
                                                    'scenario': self.scenario}
    
    def _get_pretty_name(self):
        return "%(area)s" % {'area': self.area.name}

    pretty_name = property(_get_pretty_name)
    
    class Meta:
        verbose_name = _("disabled area")
        verbose_name_plural = _("disabled areas")
        unique_together = (('scenario', 'area'),) 

    def save(self, *args, **kwargs):
        try:
            Home.objects.get(contender__scenario=self.scenario, area=self.area)
        except ObjectDoesNotExist:
            pass
        else:
            raise AreaNotAllowed(_("Selected area is controlled by a country"))
        try:
            Setup.objects.get(contender__scenario=self.scenario, area=self.area)
        except ObjectDoesNotExist as MultipleObjectsReturned:
            pass
        else:
            raise AreaNotAllowed(_("Selected area is occupied by one or more units"))
        try:
            CityIncome.objects.get(scenario=self.scenario, city=self.area)
        except ObjectDoesNotExist:
            pass
        else:
            raise AreaNotAllowed(_("Selected area has special income"))
        return super(DisabledArea, self).save(*args, **kwargs)
            
    def _get_editor(self):
        return self.scenario.editor

    editor = property(_get_editor)

class CityIncome(models.Model):
    """
    This class represents a City that generates an income in a given Scenario
    """ 
    city = models.ForeignKey(Area, verbose_name=_("city"), on_delete=models.CASCADE)
    scenario = models.ForeignKey(Scenario, verbose_name=_("scenario"), on_delete=models.CASCADE)

    def __str__(self):
        return "%s" % self.city.name

    class Meta:
        verbose_name = _("city income")
        verbose_name_plural = _("city incomes")
        unique_together = (("city", "scenario"),)

    def save(self, *args, **kwargs):
        try:
            DisabledArea.objects.get(scenario=self.scenario, area=self.city)
        except ObjectDoesNotExist:
            pass
        else:
            raise AreaNotAllowed(_("This area is disabled"))
        super(CityIncome, self).save(*args, **kwargs)

    def _get_editor(self):
        return self.scenario.editor

    editor = property(_get_editor)

income_list_validator = RegexValidator(regex="^([0-9]+,\s*){5}[0-9]+$",
        message = _("List must have 6 comma separated numbers"))

class RandomIncome(models.Model):
    income_list = models.CharField(_("income list"), max_length=20,
        validators=[income_list_validator,])
    
    class Meta:
        abstract = True

    def save(self):
        self.income_list = "".join(self.income_list.split())
        return super(RandomIncome, self).save()

    def as_list(self):
        return self.income_list.split(',')
    
    def get_ducats(self, die, double=False):
        assert die in range(1, 7)
        table = self.as_list()
        d = int(table[die - 1])
        if double:
            return d * 2
        else:
            return d

class CountryRandomIncome(RandomIncome):
    """ This class details the number of ducats that a country gets
    depending on a random integer (1-6).
    """
    setting = models.ForeignKey(Setting, verbose_name=_("setting"), on_delete=models.CASCADE)
    country = models.ForeignKey(Country, verbose_name=_("country"), on_delete=models.CASCADE)

    class Meta(RandomIncome.Meta):
        verbose_name = _("country random income")
        verbose_name_plural = _("countries random incomes")

    def __str__(self):
        return str(self.country)

class CityRandomIncome(RandomIncome):
    """ This class details the number of ducats that a city gets
    depending on a random integer (1-6).
    """
    city = models.OneToOneField(Area, verbose_name=_("city"), on_delete=models.CASCADE)

    class Meta(RandomIncome.Meta):
        verbose_name = _("city random income")
        verbose_name_plural = _("cities random incomes")

    def __str__(self):
        return str(self.city)

class Home(models.Model):
    """ This class defines which Country controls each Area in a given Scenario,
    at the beginning of a game.
    
    Note that, in some special cases, a province controlled by a country does
    not belong to the **home country** of this country. The ``is_home``
    attribute controls that.
    """

    #scenario = models.ForeignKey(Scenario, verbose_name=_("scenario"))
    #country = models.ForeignKey(Country, verbose_name=_("country"))
    contender = models.ForeignKey(Contender, verbose_name=_("contender"), on_delete=models.CASCADE)
    area = models.ForeignKey(Area, verbose_name=_("area"), on_delete=models.CASCADE)
    is_home = models.BooleanField(_("is home"), default=True)

    def __str__(self):
        return "%s" % self.area.name

    class Meta:
        verbose_name = _("home area")
        verbose_name_plural = _("home areas")
        #unique_together = (("scenario", "country", "area"),)
        unique_together = (("contender", "area"),)

    def save(self, *args, **kwargs):
        if self.contender.country is None:
            raise HomeIsAutonomous(_("You cannot define an autonomous home"))
        if self.area.is_sea:
            raise AreaNotAllowed(_("A sea area cannot be controlled"))
        try:
            DisabledArea.objects.get(scenario=self.contender.scenario, area=self.area)
        except ObjectDoesNotExist:
            try:
                Home.objects.get(contender__scenario=self.contender.scenario, area=self.area)
            except ObjectDoesNotExist:
                super(Home, self).save(*args, **kwargs)
            else:
                raise HomeIsTaken(_("This area is already controlled by another country"))
        else:
            raise AreaNotAllowed(_("This area is disabled"))

    def unique_error_message(self, model_class, unique_check):
        if model_class == type(self) and unique_check == ('contender', 'area'):
            return _("This area is already controlled by a country")
        else:
            return super(Setup, self).unique_error_message(model_class, unique_check)

    def _get_editor(self):
        return self.contender.scenario.editor

    editor = property(_get_editor)



UNIT_TYPES = (('A', _('Army')),
              ('F', _('Fleet')),
              ('G', _('Garrison'))
              )

class Setup(models.Model):
    """
    This class defines the initial setup of a unit in a given Scenario.
    """

    #scenario = models.ForeignKey(Scenario, verbose_name=_("scenario"))
    #country = models.ForeignKey(Country, blank=True, null=True,
    #   verbose_name=_("country"))
    contender = models.ForeignKey(Contender, verbose_name=_("contender"), on_delete=models.CASCADE)
    area = models.ForeignKey(Area, verbose_name=_("area"), on_delete=models.CASCADE)
    unit_type = models.CharField(_("unit type"), max_length=1,
        choices=UNIT_TYPES)
    
    def __str__(self):
        return _("%(unit)s in %(area)s") % {
            'unit': self.get_unit_type_display(),
            'area': self.area.name }

    class Meta:
        verbose_name = _("initial setup")
        verbose_name_plural = _("initial setups")

    def save(self, *args, **kwargs):
        if not self.id:
            if not self.area.accepts_type(self.unit_type):
                raise WrongUnitType(_("This unit type is not allowed in this area"))
            try:
                DisabledArea.objects.get(scenario=self.contender.scenario, area=self.area)
            except ObjectDoesNotExist:
                try:
                    Setup.objects.get(contender__scenario=self.contender.scenario, area=self.area, unit_type=self.unit_type)
                except ObjectDoesNotExist:
                    super(Setup, self).save(*args, **kwargs)
                else:
                    raise AreaIsOccupied(_("You cannot place two units of the same type on the same area"))
            else:
                raise AreaNotAllowed(_("This area is disabled"))

    def _get_editor(self):
        return self.contender.scenario.editor

    editor = property(_get_editor)

class ControlToken(models.Model):
    """ Defines the coordinates of the control token for a board area. """

    area = models.OneToOneField(Area, on_delete=models.CASCADE)
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()

    def __str__(self):
        return "%s, %s" % (self.x, self.y)


class GToken(models.Model):
    """ Defines the coordinates of the Garrison token in a board area. """

    area = models.OneToOneField(Area, on_delete=models.CASCADE)
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()

    def __str__(self):
        return "%s, %s" % (self.x, self.y)


class AFToken(models.Model):
    """ Defines the coordinates of the Army and Fleet tokens in a board area."""

    area = models.OneToOneField(Area, on_delete=models.CASCADE)
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()

    def __str__(self):
        return "%s, %s" % (self.x, self.y)

##
## Natural disasters
##

class DisasterCellManager(models.Manager):
    def roll(self, setting, row=None, column=None):
        cells = self.filter(area__setting=setting)
        chosen_ids = []
        if row:
            chosen_ids += list(cells.filter(row=row).values_list('id', flat=True))
        if column:
            chosen_ids += list(cells.filter(column=column).values_list('id', flat=True))
        return cells.filter(id__in=chosen_ids)

class DisasterCell(models.Model):
    area = models.OneToOneField(Area, verbose_name=_("area"), on_delete=models.CASCADE)
    row = models.PositiveIntegerField(_("row"))
    column = models.PositiveIntegerField(_("column"))

    objects = DisasterCellManager()
    
    class Meta:
        abstract = True

    def __str__(self):
        return "%s (%s, %s)" % (self.area, self.row, self.column)

class FamineCell(DisasterCell):
    
    class Meta(DisasterCell.Meta):
        verbose_name = _("famine cell")
        verbose_name_plural = _("famine cells")

class PlagueCell(DisasterCell):
    
    class Meta(DisasterCell.Meta):
        verbose_name = _("plague cell")
        verbose_name_plural = _("plague cells")

class StormCell(DisasterCell):
    
    class Meta(DisasterCell.Meta):
        verbose_name = _("storm cell")
        verbose_name_plural = _("storm cells")

##
## Trade routes
##

class TradeRoute(models.Model):
    #left = models.ForeignKey(Area, related_name="left_routes")
    #right = models.ForeignKey(Area, related_name="right_routes")

    class Meta:
        verbose_name = _("trade route")
        verbose_name_plural = _("trade routes")

    def __str__(self):
        return "%s" % self.id

class RouteStep(models.Model):
    route = models.ForeignKey(TradeRoute, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    is_end = models.BooleanField(default=False)

    class Meta:
        unique_together = (('route', 'area'),)
        verbose_name = _("route step")
        verbose_name_plural = _("route steps")

    def __str__(self):
        return str(self.area)
