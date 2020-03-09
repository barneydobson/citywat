#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 16 13:32:27 2019

@author: barney
"""
import constants 

def add_option(model,names):

    if isinstance(names,str):
        names = [names]
    for name in names:
        if (name == 'nopump_rule'):
            model.parameters['nopump_precip'] = 10
            model.parameters['nopump_volume'] = 192807
        elif (name == 'supply_reservoir'):
            model.parameters['reservoir_capacity'] += 24000
        elif (name == 'effluent_reuse'):
            model.parameters['effluent_reuse_capacity'] += 150
        elif (name == 'demand_reduction'):
            model.parameters['per_household_consumption'] *= 0.9 # Achieved by increased metering - 10% achieveable by about 2035
        elif (name == 'leakage'):
            model.parameters['distribution_leakage'] *= 0.65
        elif (name == 'green_roofs_equivalent'):
            #Calculate as equivalent greenspace increase
            area = 3
            assumed_runoff_reduction = 0.5
            greenspace_increase = area * assumed_runoff_reduction
            
            #Reduce percent impermeable accordingly
            imperm_area = model.parameters['area'] * model.parameters['percent_impermeable'] * constants.PCT_TO_PROP
            model.parameters['percent_impermeable'] = (imperm_area - greenspace_increase)/model.parameters['area'] * constants.PROP_TO_PCT
#        elif (name == 'green_roofs_storage'):
#            #I don't think this method makes sense - since it implies water can be stored not where it fell
#            area = 3
#            attenuation_capacity = 200
#            model.parameters['impermeable_surface_storage_capacity'] += (area * attenuation_capacity * constants.MM_KM2_TO_ML)
        elif (name == 'water_butts'):
            model.parameters['rainwater_harvesting_penetration'] = 100 # % (of households and of roof area)
            model.parameters['rainwater_harvesting_storage_capacity'] = 280 # Ml (assuming a 400L water butt for 18% of London's households)
#        elif (name == 'wwtw_rate'):
#            model.parameters['wastewater_treatment_max_rate_change'] *= 1.1
#        elif (name == 'wwtw_cap'):
#            model.parameters['wastewater_treatment_plant_maximum_capacity'] *= 1.1
        elif (name == 'wwtw_storage'):
            model.parameters['wastewater_temporary_storage_capacity'] += 150
        else:
            print('option not found')

def options_list():
    return ['nopump_rule',
            'supply_reservoir',
            'effluent_reuse',
            'demand_reduction',
            'leakage',
            'green_roofs_equivalent',
#            'green_roofs_storage',
            'water_butts',
#            'wwtw_rate',
#            'wwtw_cap',
            'wwtw_storage']