from django.conf.urls.defaults import *

import condottieri_scenarios.views as views

urlpatterns = patterns('condottieri_scenarios.views',
	url(r'^$', views.ScenarioListView.as_view(), name='scenario_list'),
	url(r'^create/$',
		views.ScenarioCreateView.as_view(), name='scenario_create'),
	url(r'^detail/(?P<slug>[-\w]+)/$',
		views.ScenarioView.as_view(), name='scenario_detail'),
	url(r'^make_map/(?P<slug>[-\w]+)/$',
		views.ScenarioRedrawMapView.as_view(), name='scenario_make_map'),
	url(r'^toggle/(?P<slug>[-\w]+)/$',
		views.ScenarioToggleView.as_view(), name='scenario_toggle'),
	url(r'^stats/(?P<slug>[-\w]+)/$',
		views.ScenarioView.as_view(template_name='condottieri_scenarios/scenario_stats.html'), name='scenario_stats'),
	url(r'^contenders/(?P<slug>[-\w]+)/$',
		views.ContenderEditView.as_view(), name='scenario_contender_edit'),
	url(r'^edit_description/(?P<slug>[-\w]+)/$',
		views.ScenarioDescriptionsEditView.as_view(), name='scenario_descriptions_edit'),
	url(r'^cityincomes/(?P<slug>[-\w]+)/$',
		views.CityIncomeEditView.as_view(), name='scenario_cityincome_edit'),
	url(r'^cityincome/delete/(?P<pk>\d+)/$',
		views.CityIncomeDeleteView.as_view(), name='scenario_cityincome_delete'),
	url(r'^disabled/(?P<slug>[-\w]+)/$',
		views.DisabledAreasEditView.as_view(), name='scenario_disabled_edit'),
	url(r'^disabled/delete/(?P<pk>\d+)/$',
		views.DisabledAreaDeleteView.as_view(), name='scenario_disabled_delete'),
	url(r'^contender/delete/(?P<pk>\d+)/$',
		views.ContenderDeleteView.as_view(), name='scenario_contender_delete'),
	url(r'^contender/homes/(?P<pk>\d+)/$',
		views.ContenderHomeView.as_view(), name='scenario_contender_homes'),
	url(r'^home/delete/(?P<pk>\d+)/$',
		views.HomeDeleteView.as_view(), name='scenario_home_delete'),
	url(r'^contender/setup/(?P<pk>\d+)/$',
		views.ContenderSetupView.as_view(), name='scenario_contender_setup'),
	url(r'^setup/delete/(?P<pk>\d+)/$',
		views.SetupDeleteView.as_view(), name='scenario_setup_delete'),
	url(r'^contender/treasury/(?P<pk>\d+)/$',
		views.ContenderTreasuryView.as_view(), name='scenario_contender_treasury'),
)

