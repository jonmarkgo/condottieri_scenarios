from django.urls import path, re_path
from django.views.generic.base import RedirectView

import condottieri_scenarios.views as views

app_name = 'scenarios'

urlpatterns = [
	path('', views.ScenarioListView.as_view(), name='scenario_list'),
	path('setting/', views.SettingListView.as_view(), name='setting_list'),
	path('setting/detail/<slug:slug>/', views.SettingView.as_view(), name='setting_detail'),
	path('setting/disasters/<slug:slug>/', views.DisasterTableView.as_view(), name='setting_disasters'),
	path('create/', views.ScenarioCreateView.as_view(), name='scenario_create'),
	path('detail/<slug:slug>/', views.ScenarioView.as_view(), name='scenario_detail'),
	path('make_map/<slug:slug>/', views.ScenarioRedrawMapView.as_view(), name='scenario_make_map'),
	path('toggle/<slug:slug>/', views.ScenarioToggleView.as_view(), name='scenario_toggle'),
	path('stats/<slug:slug>/', views.ScenarioView.as_view(template_name='condottieri_scenarios/scenario_stats.html'), name='scenario_stats'),
	path('contenders/<slug:slug>/', views.ContenderEditView.as_view(), name='scenario_contender_edit'),
	path('edit_description/<slug:slug>/', views.ScenarioDescriptionsEditView.as_view(), name='scenario_descriptions_edit'),
	path('cityincomes/<slug:slug>/', views.CityIncomeEditView.as_view(), name='scenario_cityincome_edit'),
	path('cityincome/delete/<int:pk>/', views.CityIncomeDeleteView.as_view(), name='scenario_cityincome_delete'),
	path('disabled/<slug:slug>/', views.DisabledAreasEditView.as_view(), name='scenario_disabled_edit'),
	path('disabled/delete/<int:pk>/', views.DisabledAreaDeleteView.as_view(), name='scenario_disabled_delete'),
	path('contender/delete/<int:pk>/', views.ContenderDeleteView.as_view(), name='scenario_contender_delete'),
	path('contender/homes/<int:pk>/', views.ContenderHomeView.as_view(), name='scenario_contender_homes'),
	path('home/delete/<int:pk>/', views.HomeDeleteView.as_view(), name='scenario_home_delete'),
	path('contender/setup/<int:pk>/', views.ContenderSetupView.as_view(), name='scenario_contender_setup'),
	path('setup/delete/<int:pk>/', views.SetupDeleteView.as_view(), name='scenario_setup_delete'),
	path('contender/treasury/<int:pk>/', views.ContenderTreasuryView.as_view(), name='scenario_contender_treasury'),
	path('country/', views.CountryListView.as_view(), name='country_list'),
	path('country/create/', views.CountryCreateView.as_view(), name='country_create'),
	path('country/detail/<slug:slug>/', views.CountryView.as_view(), name='country_detail'),
	path('country/edit/<slug:slug>/', views.CountryUpdateView.as_view(), name='country_edit'),
	path('country/income/delete/<int:pk>/', views.CountryRandomIncomeDeleteView.as_view(), name='country_income_delete'),
	path('area/list/<slug:slug>/', views.SettingAreasView.as_view(), name='setting_areas'),
	path('area/create/<slug:slug>/', views.AreaCreateView.as_view(), name='area_create'),
	path('area/edit/<int:pk>/', views.AreaUpdateView.as_view(), name='area_edit'),
	# Legacy URL pattern to handle old area/update/ URLs
	path('area/update/<int:pk>/', RedirectView.as_view(pattern_name='scenarios:area_edit', permanent=True), name='area_update_legacy'),
]
