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

import django.forms as forms
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _

import condottieri_scenarios.models as scenarios

class CreateScenarioForm(forms.ModelForm):
    setting = forms.ModelChoiceField(queryset=scenarios.Setting.objects.filter(enabled=True),
        label=_("Setting"))
    designer = forms.CharField(max_length=30, required=False, help_text=_("leave it blank if you are the designer"))
    title_en = forms.CharField(
        label=_("Title"),
        max_length=128,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=_("max. 128 characters")
    )
    description_en = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = scenarios.Scenario
        fields = (
            'setting',
            'title_en',
            'description_en',
            'designer',
            'start_year',)
        exclude = ('editor', 'published')

class ScenarioDescriptionsForm(forms.ModelForm):

    class Meta:
        model = scenarios.Scenario
        exclude = ('name', 'editor', 'enabled', 'countries', 'published')

class ScenarioForm(forms.ModelForm):
    class Meta:
        model = scenarios.Scenario
        fields = ( )

class CountryForm(forms.ModelForm):
    class Meta:
        model = scenarios.Country
        exclude = ('editor', 'static_name', 'protected',)
        fields = ['name_en', 'color', 'coat_of_arms', 'can_excommunicate', 'special_units', 'religion']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add the translated name field
        self.fields['name_en'] = forms.CharField(
            label=_("Name"),
            max_length=50,
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            initial=self.instance.name_en if self.instance and self.instance.pk else ''
        )

class CreateContenderForm(forms.ModelForm):
    country = forms.ModelChoiceField(queryset=scenarios.Country.objects.filter(enabled=True),
        label=_("Country"))

    class Meta:
        model = scenarios.Contender
        fields = ('country',)

    def clean(self):
        cleaned_data = self.cleaned_data
        country = cleaned_data["country"]
        scenario = cleaned_data["scenario"]
        if country.get_income(scenario.setting):
            return cleaned_data
        else:
            raise forms.ValidationError(_("You must define a variable income table for %s") % country)

class ContenderEditForm(forms.ModelForm):
    class Meta:
        model = scenarios.Contender
        fields = ( )

def homeformset_factory(setting):
    class HomeForm(forms.ModelForm):
        area = forms.ModelChoiceField(queryset=scenarios.Area.objects.filter(
            setting=setting))
    
        class Meta:
            model = scenarios.Home
            fields = "__all__"
    
    return inlineformset_factory(scenarios.Contender, scenarios.Home, form=HomeForm, extra=5, fields="__all__")

def setupformset_factory(setting):
    class SetupForm(forms.ModelForm):
        area = forms.ModelChoiceField(queryset=scenarios.Area.objects.filter(
            setting=setting))
    
        class Meta:
            model = scenarios.Setup
            fields = "__all__"
    
    return inlineformset_factory(scenarios.Contender, scenarios.Setup, form=SetupForm, extra=5, fields="__all__")

def cityincomeformset_factory(setting):
    class CityIncomeForm(forms.ModelForm):
        city = forms.ModelChoiceField(queryset=scenarios.Area.objects.major().filter(setting=setting))
    
        class Meta:
            model = scenarios.CityIncome
            fields = "__all__"

    return inlineformset_factory(scenarios.Scenario, scenarios.CityIncome, form=CityIncomeForm, extra=3, fields="__all__")

def disabledareaformset_factory(setting):
    class DisabledAreaForm(forms.ModelForm):
        area = forms.ModelChoiceField(queryset=scenarios.Area.objects.filter(setting=setting))
    
        class Meta:
            model = scenarios.DisabledArea
            fields = "__all__"

    return inlineformset_factory(scenarios.Scenario, scenarios.DisabledArea, form=DisabledAreaForm, extra=5, fields="__all__")

TreasuryFormSet = inlineformset_factory(scenarios.Contender, scenarios.Treasury, extra=1, fields="__all__")

ContenderFormSet = inlineformset_factory(scenarios.Scenario, scenarios.Contender,
    form=CreateContenderForm, extra=1, fields="__all__")

CountryRandomIncomeFormSet = inlineformset_factory(scenarios.Country,
    scenarios.CountryRandomIncome,
    extra=1,
    fields="__all__")

class AreaForm(forms.ModelForm):
    class Meta:
        model = scenarios.Area
        fields = ['code', 'is_sea', 'is_coast', 'has_city', 'is_fortified', 
                 'has_port', 'control_income', 'garrison_income', 'religion', 'mixed']
        exclude = ('setting', 'borders',)
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add the translated name field
        self.fields['name'] = forms.CharField(
            label=_("Name"),
            max_length=25,
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            initial=self.instance.name if self.instance and self.instance.pk else ''
        )
    
    def clean(self):
        cleaned_data = self.cleaned_data
        is_sea = cleaned_data.get("is_sea", False)
        is_coast = cleaned_data.get("is_coast", False)
        has_city = cleaned_data.get("has_city", False)
        is_fortified = cleaned_data.get("is_fortified", False)
        has_port = cleaned_data.get("has_port", False)
        control_income = cleaned_data.get("control_income", 0)
        garrison_income = cleaned_data.get("garrison_income", 0)
        mixed = cleaned_data.get("mixed", False)

        if not has_city:
            if is_fortified:
                raise forms.ValidationError(str(_("An area without a city cannot be fortified")))
            if has_port:
                raise forms.ValidationError(str(_("An area without a city cannot have a port")))
            if control_income > 1:
                raise forms.ValidationError(str(_("The control income for an area without city must be 1")))
            if garrison_income > 0:
                raise forms.ValidationError(str(_("The garrison income for an area without city must be 0")))
        else:
            if control_income < 2:
                raise forms.ValidationError(str(_("The control income for an area with a city must be 2 or higher")))

        if is_sea:
            if is_coast:
                raise forms.ValidationError(str(_("An area cannot be sea and coast at the same time")))
            if has_city:
                raise forms.ValidationError(str(_("There cannot be a city in a sea area")))
            if control_income > 0:
                raise forms.ValidationError(str(_("The control income for a sea area must be 0")))
            if mixed:
                raise forms.ValidationError(str(_("An area cannot be sea and mixed at the same time")))
        else:
            if control_income < 1:
                raise forms.ValidationError(str(_("The minimum control income for land areas is 1")))

        if not is_coast:
            if has_port:
                raise forms.ValidationError(str(_("An area must be a coast to have a port")))

        if is_fortified:
            if control_income - garrison_income != 1:
                raise forms.ValidationError(str(_("For an area with a fortified city, the control income must be the garrison income + 1")))
            
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Save the translated name
        instance.name = self.cleaned_data['name']
        if commit:
            instance.save()
        return instance

ControlTokenFormSet = inlineformset_factory(scenarios.Area, scenarios.ControlToken, extra=1, fields="__all__")
GTokenFormSet = inlineformset_factory(scenarios.Area, scenarios.GToken, extra=1, fields="__all__")
AFTokenFormSet = inlineformset_factory(scenarios.Area, scenarios.AFToken, extra=1, fields="__all__")
FamineCellFormSet = inlineformset_factory(scenarios.Area, scenarios.FamineCell, extra=1, fields="__all__")
PlagueCellFormSet = inlineformset_factory(scenarios.Area, scenarios.PlagueCell, extra=1, fields="__all__")
StormCellFormSet = inlineformset_factory(scenarios.Area, scenarios.StormCell, extra=1, fields="__all__")

def areaborderformset_factory(setting):
    class AreaBorderForm(forms.ModelForm):
        from_area = forms.ModelChoiceField(queryset=scenarios.Area.objects.filter(setting=setting))
    
        class Meta:
            model = scenarios.Border
            fields = "__all__"

    return inlineformset_factory(scenarios.Area, scenarios.Border, fk_name="to_area", form=AreaBorderForm, extra=5, fields="__all__")

