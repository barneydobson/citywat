# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 12:43:49 2019

@author: bdobson
"""
import constants
import initialise
import options
from tqdm import tqdm
import pandas as pd
from copy import deepcopy

class model:
    def __init__(self,addresses):
        
        """Initialise all state variables and parameters
        These are set to estimates for London
        """
        
        self.state_variables = None
        self.reset_states()
        
        self.parameters = None
        self.reset_parameters()
        
        """Load data at addresses
        """
        self.input_variables = initialise.get_inputs(addresses)
        self.parameters['ltoa'] = initialise.get_ltoa(addresses)
        
        """Define timestep functions
        Define the set of functions each of which represents a different process in a timestep
        """
        self.model_list = initialise.get_models()
    
    def reset_states(self):
        #Resets state variables to initial ones
        self.state_variables = initialise.get_state_variables()        
        
    def reset_parameters(self):
        #Resets state variables to initial ones
        self.parameters = initialise.get_parameters()        
        
    def change_parameter(self, *args):
        
        #Iterate over parameter-value pairs to set new values
        i = 0
        
        while i < len(args):
            if isinstance(args[i],str):
                self.parameters[args[i]] = args[i+1]
            else:
                print('Error: args must be provided in parameter-value pairs \n(e.g. \nget_parameters("area",1200)\n)\n\nReturning None')
                return None
            i+=2
    
    def change_state_variable(self, *args):
        
        #Iterate over state_variable-value pairs to set new values
        i = 0
        
        while i < len(args):
            if isinstance(args[i],str):
                self.state_variables[args[i]] = args[i+1]
            else:
                print('Error: args must be provided in parameter-value pairs \n(e.g. \nget_parameters("area",1200)\n)\n\nReturning None')
                return None
            i+=2
            
    def add_model(self, args):
        
        #Append new models to list
        self.model_list.append(args)
    
    def remove_model(self,args):
        #Check that models are in list and remove them
        for fn in args:
            if fn in self.model_list:
                self.model_list.remove(fn)
            else:
                print('Warning: ' + str(fn) + ' not found in model_list')
    
    def copy(self):
        #Copy a model
        return deepcopy(self)
    
    def add_option(self,names):
        #Call the add_option function to implement options in the model
        options.add_option(self,names)
    
    def run(self,fast = None):
        state_variables_timevarying = [] # state_variables is stored in this at the beginning of every timestep
        
        if fast is not True:
            #Iterate over all dates
            for date in tqdm(self.input_variables.index):
                
                #Set date
                self.state_variables['date'] = date
                
                #Store input variables in state variables
                for input_var in self.input_variables.columns:
                    self.state_variables[input_var] = self.input_variables.loc[date, input_var]
                    
                #Iterate over model list
                for fn in self.model_list:
                    fn(self.state_variables,self.parameters)
                    
                #Store state variables
                state_variables_timevarying.append(self.state_variables.copy())
        else:
            #A ~2x faster but less readable version of run
            dates = self.input_variables.index
            values = self.input_variables.values
            value_names = self.input_variables.columns
            
            #Iterate over all dates
            for i in tqdm(range(0,len(dates))):
                
                #Set date
                self.state_variables['date'] = dates[i]
                
                #Store input variables in state variables
                for j in range(0,len(value_names)):
                    self.state_variables[value_names[j]] = values[i,j]
        
                #Iterate over model list
                for fn in self.model_list:
                    fn(self.state_variables,self.parameters)
    
                #Store state variables
                state_variables_timevarying.append(self.state_variables.copy())
                
        #Return dataframe of results
        return pd.DataFrame(state_variables_timevarying).set_index('date')

def abstraction(state_variables, parameters): 
    #Evaluate LTOA
    pct_full = state_variables['reservoir_volume']/parameters['reservoir_capacity']
    levels = parameters['ltoa']['levels'][state_variables['date'].month - 1]
    mrfs = parameters['ltoa']['mrfs'][state_variables['date'].month - 1]
    
    if pct_full > levels[0]:
        state_variables['restrictions'] = 0
        state_variables['river_minimum_flow'] = mrfs[0]
    elif pct_full > levels[1]:
        state_variables['restrictions'] = 0
        state_variables['river_minimum_flow'] = mrfs[1]
    elif pct_full > levels[2]:
        state_variables['restrictions'] = 1
        state_variables['river_minimum_flow'] = mrfs[1]
    elif pct_full > levels[3]:
        state_variables['restrictions'] = 2
        state_variables['river_minimum_flow'] = mrfs[2]
    elif pct_full > levels[4]:
        state_variables['restrictions'] = 3
        state_variables['river_minimum_flow'] = mrfs[3]
    else:
        state_variables['restrictions'] = 4
        state_variables['river_minimum_flow'] = mrfs[3]
    
    #Available flow for abstraction
    flow = state_variables['flow'] #Store in variable to improve performance
    flow_upstream_of_teddington = flow -\
                                    parameters['upstream_abstractions'] +\
                                    state_variables['treated_effluent_to_abstraction_point'] +\
                                    parameters['upstream_inflows']
    flow_above_mrf = max(flow_upstream_of_teddington - state_variables['river_minimum_flow'],0)
    
    #Find target abstraction
    if state_variables['restrictions'] == 0:
        target_abstraction = parameters['target_river_abstraction_above_L1']
    else:
        target_abstraction = parameters['target_river_abstraction_below_L1']
    
    #Don't overabstact more than the maximum beneficial abstraction
    target_abstraction = min(target_abstraction,parameters['reservoir_capacity'] - \
                                                 state_variables['reservoir_volume'] +\
                                                 state_variables['freshwater_treatment_plant_demand'] -\
                                                 parameters['target_groundwater_abstraction'])
    
    #Apply nopump_rule
    if (state_variables['reservoir_volume'] > parameters['nopump_volume']) & (state_variables['precipitation'] > parameters['nopump_precip']):
        target_abstraction = 0
    
    #Calculate actual river abstraction
    target_abstraction = min(target_abstraction,flow_above_mrf)
    state_variables['river_to_freshwater_treatment'] = max(target_abstraction -\
                                                            (parameters['reservoir_capacity'] -\
                                                            state_variables['reservoir_volume'])
                                                            ,0)
    state_variables['river_to_reservoir'] = target_abstraction - state_variables['river_to_freshwater_treatment']
    state_variables['reservoir_volume'] += state_variables['river_to_reservoir']
    
    state_variables['denaturalised_teddington_flow'] = flow -\
                                                        state_variables['river_to_freshwater_treatment'] -\
                                                        state_variables['river_to_reservoir']
    
    #Double check MRF
    if (state_variables['denaturalised_teddington_flow'] < state_variables['river_minimum_flow']) & (state_variables['river_to_reservoir'] + state_variables['river_to_freshwater_treatment'] > 0):
        print('MRF overabstraction at : ' + state_variables['date'].strftime('%Y-%m-%d'))

def release(state_variables, parameters): 
    #Calculate target reservoir release
    target_reservoir_to_treatment = state_variables['freshwater_treatment_plant_demand'] -\
                                        state_variables['river_to_freshwater_treatment'] -\
                                        parameters['target_groundwater_abstraction']
    
    #Aim to not draw below control curve, increase groundwater abstraction if necessary
    distance_above_L1 = state_variables['reservoir_volume'] -\
                         parameters['reservoir_capacity'] *\
                         parameters['ltoa']['levels'][state_variables['date'].month - 1][1] -\
                         target_reservoir_to_treatment
    if distance_above_L1 < 0:
        state_variables['groundwater_to_freshwater_treatment'] = min(parameters['available_groundwater_abstraction'],\
                                                                     max(-distance_above_L1,parameters['target_groundwater_abstraction']))
        target_reservoir_to_treatment -= state_variables['groundwater_to_freshwater_treatment']
    else:
        state_variables['groundwater_to_freshwater_treatment'] = parameters['target_groundwater_abstraction']
    
    #Implement release
    state_variables['reservoir_to_freshwater_treatment'] = min(target_reservoir_to_treatment,state_variables['reservoir_volume'])
    state_variables['reservoir_volume'] -= state_variables['reservoir_to_freshwater_treatment']
    
    #Double check treatment is not oversatisfied
    if (state_variables['reservoir_to_freshwater_treatment'] + state_variables['groundwater_to_freshwater_treatment'] + state_variables['river_to_freshwater_treatment']) > state_variables['freshwater_treatment_plant_demand']:
        print('Treatment oversatisfied at :' + state_variables['date'].strftime('%Y-%m-%d'))
        
    #Double check reservoir is not overfilled
    if state_variables['reservoir_volume'] > parameters['reservoir_capacity']:
        print('Reservoir overfilled at : ' + state_variables['date'].strftime('%Y-%m-%d'))
    if state_variables['reservoir_volume'] < 0 :
        print('Reservoir < 0 at : ' + state_variables['date'].strftime('%Y-%m-%d'))
    if state_variables['reservoir_to_freshwater_treatment'] + state_variables['groundwater_to_freshwater_treatment'] > state_variables['freshwater_treatment_plant_demand']:
        print('Freshwater treatment oversuppled at : ' + state_variables['date'].strftime('%Y-%m-%d'))

def calculate_consumer_demand(state_variables, parameters): 
    #Calculate demand
    baseline_demand = parameters['number_of_households'] *\
                       parameters['per_household_consumption'] * constants.L_TO_ML +\
                       parameters['non_household_consumption']
                       
    #Check whether to enact restrictions
    baseline_demand *= (1 - parameters['restrictions_pct_reduction'][state_variables['restrictions']] * constants.PCT_TO_PROP)
    
    #Apply seasonal demand profile
    demand = baseline_demand*parameters['demand_profile'][state_variables['date'].month - 1]
    
    #If it's not raining, satisfy demand with rainfall
    rainfall_demand = demand * parameters['percent_of_demand_satisfiable_by_rainfall'] * constants.PCT_TO_PROP
    if state_variables['precipitation'] < 1:
        state_variables['supplied_by_harvested'] = min(state_variables['rainwater_harvesting_volume'],rainfall_demand)
    else:
        state_variables['supplied_by_harvested'] = 0
        
    demand -= state_variables['supplied_by_harvested']
    state_variables['rainwater_harvesting_volume'] -= state_variables['supplied_by_harvested']
    state_variables['consumer_demand'] = demand

def calculate_distribution_demand(state_variables, parameters):
    #Calculate distribution demand
    state_variables['distribution_demand'] = state_variables['consumer_demand']/(1 - parameters['distribution_leakage']*constants.PCT_TO_PROP)


def freshwater_treatment(state_variables, parameters): 
    #Find WTW input and losses
    treatment_input = state_variables['reservoir_to_freshwater_treatment'] + \
                       state_variables['river_to_freshwater_treatment'] +\
                       state_variables['groundwater_to_freshwater_treatment']
    
    state_variables['freshwater_treatment_losses'] = treatment_input*parameters['freshwater_treatment_processing_losses']*constants.PCT_TO_PROP
    
    #Calculate WTW output, first fill service reservoirs and send remainder to distribution
    treatment_output = treatment_input - state_variables['freshwater_treatment_losses']
    state_variables['treatment_output_to_service_reservoirs'] = min(parameters['service_reservoir_capacity'] - state_variables['service_reservoir_volumes'], treatment_output)
    state_variables['service_reservoir_volumes'] += state_variables['treatment_output_to_service_reservoirs']
    
    #Update WTW demand
    target_demand = state_variables['distribution_demand'] + max(parameters['service_reservoir_capacity'] - state_variables['service_reservoir_volumes'],0)
    target_demand = min(target_demand,parameters['freshwater_treatment_maximum_capacity'])
    target_demand = max(target_demand,parameters['freshwater_treatment_minimum_capacity'])
    target_demand = min(target_demand,state_variables['freshwater_treatment_plant_demand'] + parameters['freshwater_treatment_max_rate_change'])
    target_demand = max(target_demand,state_variables['freshwater_treatment_plant_demand'] - parameters['freshwater_treatment_max_rate_change'])
    state_variables['freshwater_treatment_plant_demand'] = target_demand + state_variables['freshwater_treatment_losses'] # should losses go here or before? 


def distribution(state_variables, parameters):    
    #Take any extra needed water from service reservoirs
    target_from_service_reservoirs = state_variables['distribution_demand']
    target_from_service_reservoirs = min(target_from_service_reservoirs,state_variables['service_reservoir_volumes'])
    state_variables['service_reservoir_volumes'] -= target_from_service_reservoirs
    
    if state_variables['service_reservoir_volumes'] > parameters['service_reservoir_capacity']:
        print('Service reservoir volumes > capacity at : ' + state_variables['date'].strftime('%Y-%m-%d'))
    if state_variables['service_reservoir_volumes'] < 0:
        print('Service reservoir volumes < 0 at : ' + state_variables['date'].strftime('%Y-%m-%d'))
    
    state_variables['distribution_input'] = target_from_service_reservoirs

    #Split distribution input between leakage and households    
    state_variables['distribution_leakage'] = state_variables['distribution_input'] * parameters['distribution_leakage']*constants.PCT_TO_PROP
    state_variables['consumer_supplied'] = state_variables['distribution_input'] - state_variables['distribution_leakage']
    
    
    if state_variables['distribution_input'] > parameters['distribution_network_capacity']:
        print('distribution_input > distribution_network_capacity at : ' + state_variables['date'].strftime('%Y-%m-%d'))
    

def calculate_household_output(state_variables, parameters): 
    state_variables['household_output'] = state_variables['consumer_supplied']*(1-parameters['household_percentage_non_returned']*constants.PCT_TO_PROP)

def urban_runoff(state_variables, parameters): 
    precipitation_over_london = state_variables['precipitation'] * parameters['area'] * constants.MM_KM2_TO_ML
    
    impermeable_precipitation = precipitation_over_london * parameters['runoff_coefficient'] * constants.PCT_TO_PROP
    
    #Update rainwater harvesting roofs
    harvested_roof_precipitation = impermeable_precipitation * parameters['rainwater_harvesting_roof_area']
    harvested_roof_spill = max(state_variables['rainwater_harvesting_volume'] - parameters['rainwater_harvesting_storage_capacity'] + harvested_roof_precipitation,0)
    harvested_roof_precipitation -= harvested_roof_spill
    state_variables['harvested_roof_spill'] = harvested_roof_spill
    impermeable_precipitation -= harvested_roof_precipitation
    state_variables['rainwater_harvesting_volume'] += harvested_roof_precipitation
    
    #Update volume of impermeable storage and its dissipation, noting runoff
    state_variables['impermeable_surface_storage_volume'] += impermeable_precipitation
    state_variables['impermeable_surface_storage_volume'] = max(state_variables['impermeable_surface_storage_volume'] - parameters['impermeable_surface_storage_dissipation_rate'],0)
    impermeable_runoff = max(state_variables['impermeable_surface_storage_volume'] - parameters['impermeable_surface_storage_capacity'],0)    
    state_variables['impermeable_surface_storage_volume'] -= impermeable_runoff
    
    state_variables['natural_stormwater_storage_volume'] += precipitation_over_london * (1 - parameters['runoff_coefficient'] * constants.PCT_TO_PROP)
    
    #Update volume of natural storage and its dissipation, noting runoff
    state_variables['natural_stormwater_storage_volume'] = max(state_variables['natural_stormwater_storage_volume'] - parameters['natural_stormwater_storage_dissipation_rate'],0)
    natural_storage_overflow = max(state_variables['natural_stormwater_storage_volume'] - parameters['natural_stormwater_storage_capacity'],0)
    state_variables['natural_stormwater_storage_volume'] -= natural_storage_overflow
    
    #Calculate volume into sewerage
    state_variables['stormwater_into_sewerage'] = impermeable_runoff
    
    #Calculate surface water flooding
    state_variables['natural_stormwater_overflow'] = natural_storage_overflow
    
def sewerage(state_variables, parameters): 
    #Calculate how much of the stormwater cannot enter the sewerage network    
    target_sewerage_input = state_variables['household_output'] + state_variables['stormwater_into_sewerage']
    state_variables['stormwater_overflow'] = max(target_sewerage_input - parameters['sewerage_input_capacity'],0)
    target_sewerage_input -= state_variables['stormwater_overflow']
    
    #Update sewerage leakage and output
    state_variables['sewerage_leakage'] = target_sewerage_input * constants.PCT_TO_PROP
    state_variables['sewerage_output'] = target_sewerage_input - state_variables['sewerage_leakage']
    
def cso(state_variables, parameters): 
    #Calculate excess stormwater storage capacity
    wwtw_storage_excess_capacity = parameters['wastewater_temporary_storage_capacity'] -\
                                    state_variables['wastewater_temporary_storage_volume']

    #Max treatment input
    max_wwtw_input = min(state_variables['wastewater_treatment_input'] +\
                          parameters['wastewater_treatment_max_rate_change'],
                          parameters['wastewater_treatment_plant_maximum_capacity'])
                         
    
    #Excess stormwater goes untreated
    state_variables['untreated_effluent'] = max(state_variables['sewerage_output'] -\
                                                 wwtw_storage_excess_capacity -\
                                                 max_wwtw_input,\
                                                 0)
    wwtw_storage_and_plant_input = state_variables['sewerage_output'] -\
                                    state_variables['untreated_effluent']
    
    #Plant takes input and any storage that it can                               
    state_variables['wastewater_treatment_input'] = min(wwtw_storage_and_plant_input +\
                                                         state_variables['wastewater_temporary_storage_volume'],\
                                                         max_wwtw_input)
    state_variables['wastewater_temporary_storage_volume'] -= (state_variables['wastewater_treatment_input'] -\
                                                               wwtw_storage_and_plant_input)
    
def wastewater_treatment(state_variables, parameters): 
    state_variables['wastewater_treatment_losses'] = state_variables['wastewater_treatment_input'] *\
                                                      parameters['wastewater_treatment_plant_processing_losses'] *\
                                                      constants.PCT_TO_PROP
    state_variables['treated_effluent'] = state_variables['wastewater_treatment_input'] -\
                                           state_variables['wastewater_treatment_losses']
    
def wastewater_reuse(state_variables, parameters):
    state_variables['treated_effluent_to_abstraction_point'] = min(parameters['effluent_reuse_capacity'],\
                                                                    state_variables['treated_effluent'] *\
                                                                    parameters['effluent_reuse_rate'] *\
                                                                    constants.PCT_TO_PROP)
    state_variables['treated_effluent'] -= state_variables['treated_effluent_to_abstraction_point']

def water_quality(state_variables, parameters): 
    #Apply concentration parameters to flows, changing the concentration in proportion to the flow
    total_flow = state_variables['treated_effluent'] +\
                  state_variables['untreated_effluent'] +\
                  state_variables['denaturalised_teddington_flow']
    
    state_variables['treated_effluent_conc'] = state_variables['treated_effluent']/total_flow
    state_variables['untreated_effluent_conc'] = state_variables['untreated_effluent']/total_flow
    state_variables['raw_river_conc'] = state_variables['denaturalised_teddington_flow']/total_flow
    
    state_variables['dissolved_oxygen'] = (state_variables['treated_effluent'] *\
                                           parameters['treated_effluent_dissolved_oxygen'] +\
                                           state_variables['untreated_effluent'] *\
                                           parameters['untreated_effluent_dissolved_oxygen'] +\
                                           state_variables['denaturalised_teddington_flow'] *\
                                           parameters['upstream_dissolved_oxygen']) /\
                                           total_flow
                                           
    state_variables['nitrates'] = (state_variables['treated_effluent'] *\
                                   parameters['treated_effluent_nitrates'] +\
                                   state_variables['untreated_effluent'] *\
                                   parameters['untreated_effluent_nitrates'] +\
                                   state_variables['denaturalised_teddington_flow'] *\
                                   parameters['upstream_nitrates']) /\
                                   total_flow    
                                   
    state_variables['phosphorus'] = (state_variables['treated_effluent'] *\
                                     parameters['treated_effluent_phosphorus'] +\
                                     state_variables['untreated_effluent'] *\
                                     parameters['untreated_effluent_phosphorus'] +\
                                     state_variables['denaturalised_teddington_flow'] *\
                                     parameters['upstream_phosphorus']) /\
                                     total_flow                                       

