#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 10 10:46:08 2019

@author: bdobson
"""
import models
import pandas as pd
import constants

def get_ltoa(addresses):
    
    #Load lower thames operating agreement data (source: 10.1029/2018WR022865 figure 1)
    df = pd.read_csv(addresses['ltoa_address'],sep=',')
    ltoa = {
            'levels' : df.filter(regex='level').values,
            'mrfs' : df.filter(regex='mrf').values,
            }
    return ltoa

def get_inputs(addresses):
    
    #Load and intersect flow data
    flowt = pd.read_csv(addresses['flow_address_teddington'],sep=',').set_index('date')
    flowl = pd.read_csv(addresses['flow_address_lee'],sep=',').set_index('date')
    ind = flowt.index.intersection(flowl.index)
    
    #Combine in input variables    
    input_variables = {
                                'flow' : flowt.loc[ind] + flowl.loc[ind].values, # naturalised flow at Teddington Weir (m3/s)
                                'precipitation' :  pd.read_csv(addresses['precip_address'],sep=',').set_index('date') # Average precipitation across the Mogden WWRZ (mm)
                            }
    
    #join and convert input variables
    input_variables = pd.concat(input_variables,axis=1,sort=False)
    input_variables.columns = input_variables.columns.droplevel(1)
    input_variables = input_variables.dropna(axis=0,how='any')
    input_variables.flow *= constants.M3_S_TO_ML_D
    input_variables.index = pd.to_datetime(input_variables.index)
    return input_variables

def get_parameters():
    
    #Set default parameters below
    return {
            'ltoa' : None,
            'restrictions_pct_reduction' : [0,2.2,9.1,13.3,31.3], # % (source: 10.1029/2018WR022865 table 1)
            'target_river_abstraction' : 5000, # Ml/d
            'target_groundwater_abstraction' : 300, # Ml/d
            'available_groundwater_abstraction' : 500, # Ml/d
            'reservoir_capacity' : 194755, # Ml (source: 10.1029/2018WR022865 table 1)
            'service_reservoir_capacity' : 10000, # Ml
            'upstream_abstractions' : 500, # Ml/d
            'release_capacity' : 5000, # Ml/d
            'freshwater_treatment_maximum_capacity' : 3000, # Ml/d
            'freshwater_treatment_minimum_capacity' : 1500, # Ml/d
            'freshwater_treatment_processing_losses' : 2, # %
            'number_of_households' : 3500000, # int
            'per_household_consumption' : 360, # l/d
            'freshwater_treatment_max_rate_change' : 500, # Ml/d (for both increases and decreases)
            'non_household_consumption' : 375, # Ml/d
            'demand_profile' : [0.989,0.977,0.965,0.964,1.006,1.014,1.043,1.056,1.001,0.9746,0.9897,1.02], # %/100/month
            'natural_stormwater_storage_capacity' : 80000, # Ml (assuming 170mm of water storage per m2 over greenspaces)
            'natural_stormwater_storage_dissipation_rate' : 800, # Ml/d (assuming 1.5mm/d evapotranspiration per m2 over greenspaces)
            'impermeable_surface_storage_capacity' : 2350, # Ml (assuming 5mm of water storage per m2 over impermeable spaces)
            'impermeable_surface_storage_dissipation_rate' : 800, # Ml/d (assuming 1.5mm/d evapotranspiration per m2 over impermeable spaces)
            'rainwater_harvesting_storage_capacity' : 0, # Ml
            'rainwater_harvesting_penetration' : 0, # % households
            'roof_area' : 160, # km2
            'percent_of_demand_satisfiable_by_rainfall' : 8, # % (WRMP management tables show ~4% of demand is for external use. Given that it rains more than is evaporated ~50% of days, we double this to get actual demand)
            'garden_area' : 350, # km2 (source?)
            'distribution_network_capacity' : 3000, # Ml/d
            'distribution_leakage' : 20, # %
            'household_percentage_non_returned' : 10, # %
            'percent_impermeable' : 53, # % (mayor of London's office)
            'area' : 1000, # km2
            'sewerage_leakage' : 20, # %
            'sewerage_input_capacity' : 10000, # Ml/d (very dodgy estimate based on the sewer being designed for a 6mm/hr storm but would flood at 6.5mm/hr)
            'effluent_reuse_rate' : 15, # % (the % of effluent that can be reused)
            'effluent_reuse_capacity' : 0, # Ml/d
            'wastewater_treatment_plant_maximum_capacity' : 6000, # Ml/d (no minimum capacity because I don't know how that would work, source: https://www.whatdotheyknow.com/request/capacity_of_londons_sewage_treat)
            'wastewater_treatment_max_rate_change' : 1000, # Ml/d (for increases only)
            'wastewater_treatment_plant_processing_losses' : 10, # %
            'wastewater_temporary_storage_capacity' : 2000, # Ml
            'treated_effluent_phosphorus' : 2, # mg/l
            'untreated_effluent_phosphorus' : 5, # mg/l
            'upstream_phosphorus' : 0.2, # mg/l
            'nopump_precip' : 1000, # mm
            'nopump_flow' : 0, # Ml/d
            'nopump_volume' : 0 # Ml/d
            }

def get_state_variables():
    
    #Set default state variables below
    return {
            'date' : None, # date
            'flow' : None, # Ml/d
            'precipitation' : None, #Ml/d
            'consumer_demand' : 1600, # Ml/d
            'consumer_supplied' : 1500, # Ml/d
            'denaturalised_teddington_flow' : 7000, # Ml/d (i.e. flow after abstraction)
            'distribution_demand' : 1900, # Ml/d
            'distribution_input' : 1900, # Ml/d
            'distribution_leakage' : 380, # Ml/d
            'freshwater_treatment_losses' : 40, # Ml/d
            'freshwater_treatment_plant_demand' : 1940, # Ml/d
            'groundwater_to_freshwater_treatment' : 300, # Ml/d
            'harvested_roof_spill' : 0, #Ml/d
            'household_consumed' : 0, #Ml/d
            'household_output' : 1300, # Ml/d
            'impermeable_surface_storage_dissipation' : 0, # Ml/d
            'natural_stormwater_storage_dissipation' : 0, # Ml/d
            'natural_stormwater_storage_volume' : 4000, # Ml
            'natural_stormwater_overflow' : 0, #Ml/d
            'impermeable_surface_storage_volume' : 0, # Ml
            'outdoor_demand' : 0, # Ml/d
            'phosphorus' : 0.04, # mg/l
            'rainwater_harvesting_volume' : 0, #Ml
            'raw_river_conc' : 0.669, # l/l
            'reservoir_to_freshwater_treatment' : 200, # Ml/d
            'reservoir_volume' : 185000, # Ml
            'restrictions' : 0, # day
            'river_minimum_flow' : 800, # Ml/d
            'river_to_freshwater_treatment' : 1400, # Ml/d
            'river_to_reservoir' : 200, # Ml/d
            'service_reservoir_volumes' : 8000, # Ml/d
            'sewerage_leakage' : 20, # Ml/d
            'sewerage_output' : 2100, # Ml/d
            'stormwater_into_sewerage' : 800, # Ml/d
            'stormwater_overflow' : 5, # Ml/d
            'supplied_by_harvested' : 0, # Ml/d
            'treated_effluent' : 1950, # Ml/d
            'treated_effluent_conc' : 0.334, # l/l
            'treated_effluent_to_abstraction_point' : 0, # Ml/d
            'treated_used_outdoors' : 0, #Ml/d
            'treatment_output_to_service_reservoirs' : 1900, # Ml/d
            'treatment_output_to_distribution' : 0, # Ml/d
            'untreated_effluent' : 10, # Ml/d
            'untreated_effluent_conc' : 0.003, # l/l
            'upstream_abstractions' : 500, #Ml/d
            'wastewater_temporary_storage_volume' : 200, # Ml
            'wastewater_treatment_input' : 2070, # Ml/d
            'wastewater_treatment_losses' : 200, # Ml/d
            }        


def get_models():
    
    #Set default model list
    return [models.abstraction,
            models.release,
            models.calculate_consumer_demand,
            models.calculate_distribution_demand,
            models.freshwater_treatment,
            models.distribution,
            models.calculate_household_output,
            models.urban_runoff,
            models.sewerage,
            models.cso,
            models.wastewater_treatment,
            models.wastewater_reuse,
            models.water_quality]