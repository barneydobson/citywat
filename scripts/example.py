# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 16:48:00 2020

@author: bdobson
"""

import os
import pandas as pd
from matplotlib import pyplot as plt
import models
import misc

#Data addresses
repo_address = os.path.join("C:\\","Users","bdobson","Documents","GitHub","citywat")

precip_address = os.path.join(repo_address,"data","beckton_rainfall_1900_2018_day_25_km.csv")
flow_address_teddington = os.path.join(repo_address,"data","teddington-gauge-39001-naturalised.csv")
flow_address_lee = os.path.join(repo_address,"data","lee-gauge-38001-naturalised.csv")
ltoa_address = os.path.join(repo_address,"data","ltoa.csv")

output_address = os.path.join(repo_address,"outputs")

addresses = {'precip_address' : precip_address,
             'flow_address_teddington' : flow_address_teddington,
             'flow_address_lee' : flow_address_lee,
             'ltoa_address' : ltoa_address,
        }

#Load historic volume data
historic_volume_address = os.path.join(repo_address,"data","historic-volumes-traced.csv")
volumes = pd.read_csv(historic_volume_address, sep=',')
volumes.date = pd.to_datetime(volumes.date)
volumes = volumes.set_index('date')
volumes = volumes.rename(columns={'warms':'WARMS', 'wathnet':'WATHNET'})
volumes.index.name = 'Date (day)'

#Create and run the combined model
normal_model = models.model(addresses)
normal_model_results = normal_model.run(fast=True)
volumes['citywat'] = normal_model_results.loc[volumes.index,['reservoir_volume','service_reservoir_volumes']].sum(axis=1)
volumes.div(1000).plot()
plt.ylabel('Supply Reservoir Volume (Gigalitre)')
plt.savefig(os.path.join(output_address,"historic_volume.png"))

#Plot untreated effluent against precipitation and reservoir volume
ind = (normal_model_results.precipitation > 10) & (normal_model_results.reservoir_volume > 192807)

f, ax = plt.subplots(2,1,figsize=(4.6,7))
ax[0].scatter(normal_model_results.precipitation,normal_model_results.untreated_effluent_conc,facecolor='black',s=1.5,marker='.')
ax[0].scatter(normal_model_results.loc[ind].precipitation,normal_model_results.loc[ind].untreated_effluent_conc,facecolor='red',s=1.5,marker='.')
ax[0].set_xlabel('precipitation')
ax[0].set_ylabel('untreated_effluent_conc')


ax[1].scatter((normal_model_results.reservoir_volume + normal_model_results.service_reservoir_volumes)/1000,normal_model_results.untreated_effluent_conc,facecolor='black',s=1.5,marker='.')
ax[1].scatter((normal_model_results.loc[ind].reservoir_volume + normal_model_results.loc[ind].service_reservoir_volumes)/1000,normal_model_results.loc[ind].untreated_effluent_conc,facecolor='red',s=1.5,marker='.')
ax[1].set_xlabel('volume')
ax[1].set_ylabel('untreated_effluent_conc')

f.savefig(os.path.join(output_address,"precip_vol.png"))

#Get total spill
subset = normal_model_results.untreated_effluent
subset.index = pd.to_datetime(subset.index)
average_annual_spill = subset.resample('Y').sum().mean()
average_annual_spill /= 1000 #in Mm3 - the units other things seem to use
print(str(average_annual_spill))

#Create and run a water supply only model
supply_only_model = models.model(addresses)
supply_only_model.remove_model([models.calculate_household_output,
                                models.urban_runoff,
                                models.sewerage,
                                models.cso,
                                models.wastewater_treatment,
                                models.wastewater_reuse])
supply_only_model_results = supply_only_model.run(fast=True)

#Create and run a wastewater only model, and compare with normal model
wastewater_model = models.model(addresses)
wastewater_model.remove_model([models.abstraction,
                               models.release,
                               models.freshwater_treatment])

def average_abstraction(state_variables,parameters):
    state_variables['denaturalised_teddington_flow'] = state_variables['flow']

wastewater_model.model_list.insert(0,average_abstraction)
    
def reset_service_reservoirs(state_variables, parameters):
    
    #A simple model to assume demand can always be met
    state_variables['service_reservoir_volumes'] = parameters['service_reservoir_capacity']

wastewater_model.model_list = [reset_service_reservoirs] + wastewater_model.model_list
    

wastewater_model_results = wastewater_model.run(fast=True)

#Compare results
col=['r','b','c']
f = misc.water_quality_plots([normal_model_results,
                 supply_only_model_results,
                 wastewater_model_results],ind=volumes.index,color=col,lw=[0.3,1,0.3,0.3],ls = ['-','-',':'])
f.savefig(os.path.join(output_address, "water_quality_framing.png"))

#Abstraction effluent dilution
aed_model = models.model(addresses)
aed_model.add_option(['nopump_rule'])
aed_model_results = aed_model.run(fast=True)

f = misc.aed_plots([normal_model_results,
                 aed_model_results],ind=volumes.index,color=['r','b'],lw=[0.3,1,1,1],ls = ['-','-'], plot_order= [0,0,1,1])
f.savefig(os.path.join(output_address, "abstraction_effluent_dilution.png"))

mean_vol = aed_model_results['reservoir_volume'].mean() - normal_model_results['reservoir_volume'].mean()
print('vol diff : ' + str(mean_vol))

#days estimate
for level in range(1,5):
    n_jmo = sum(aed_model_results.restrictions == level)
    n_normal = sum(normal_model_results.restrictions == level)
    print('Level ' + str(level) + ', JMO - normal: ' + str(n_jmo - n_normal))

#Work out stormwater storage increase equivalent
storm_model = models.model(addresses)
storm_model.parameters['wastewater_temporary_storage_capacity'] *= 1.06
storm_model_results = storm_model.run(fast = True)
storm_mean = storm_model_results.untreated_effluent_conc.mean()

print(aed_model_results.untreated_effluent_conc.mean())
print(storm_mean)

#Evaluate options
options_results = []
options_list = normal_model.options_list()
for option in options_list:
    option_model = models.model(addresses)
    option_model.add_option(option)
    result = option_model.run(fast=True)
    options_results.append((normal_model_results - result).mean())
options_results = pd.concat(options_results, axis = 1, sort = False)
options_results.columns = options_list

#Plot relevant subset
subset = options_results.loc[['reservoir_volume',
                                'restrictions',
                                'raw_river_conc',
                                'treated_effluent_conc',
                                'untreated_effluent_conc',
                                'phosphorus']]

f = misc.colorgrid_plot(-subset.copy())
f.savefig(os.path.join(output_address, "colorgrid_results.png"))