# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 16:48:00 2020

@author: bdobson
"""

import os
import pandas as pd
from matplotlib import pyplot as plt
import sys
sys.path.append(os.path.join("C:\\","Users","bdobson","Documents","GitHub","citywat","scripts"))
import models
import misc
import numpy as np

#Data addresses
repo_address = os.path.join("C:\\","Users","bdobson","Documents","GitHub","citywat")

precip_address = os.path.join(repo_address,"data","beckton_rainfall_1900_2018_day_25_km.csv")
flow_address_teddington = os.path.join(repo_address,"data","upstream_thames_naturalised.csv")
flow_address_lee = os.path.join(repo_address,"data","upstream_lee_naturalised.csv")
ltoa_address = os.path.join(repo_address,"data","ltoa.csv")
upstream_phos_address = os.path.join(repo_address,"data","thames_upstream_phosphorus.csv")
wwtw_phos_address = os.path.join(repo_address,"data","average_wwtw_phosphorus.csv")


output_address = os.path.join(repo_address,"outputs")

addresses = {'precip_address' : precip_address,
             'flow_address_teddington' : flow_address_teddington,
             'flow_address_lee' : flow_address_lee,
             'ltoa_address' : ltoa_address,
             'phos_address' : upstream_phos_address,
             'wwtw_phos_address' : wwtw_phos_address
        }

#Load historic volume data
historic_volume_address = os.path.join(repo_address,"data","historic-volumes-traced.csv")
volumes = pd.read_csv(historic_volume_address, sep=',')
volumes.date = pd.to_datetime(volumes.date)
volumes = volumes.set_index('date')
volumes = volumes.rename(columns={'warms':'WARMS', 'wathnet':'WATHNET'})
volumes.index.name = 'Date (day)'

#Create and run the combined model, comparing against historic data
normal_model = models.model(addresses)
normal_model_results = normal_model.run(fast=True)
volumes['CityWat'] = normal_model_results.loc[volumes.index,['reservoir_volume','service_reservoir_volumes']].sum(axis=1)
f, axs = plt.subplots(2,1,figsize=(4.6,7))
#fontsize = 6.5
col = ['r','b','c']
for (color, (name,data)) in zip(col,volumes.iteritems()):
    axs[0].plot(data.div(1000),color=color,lw=1)
    #axs[0].set_ylabel('Supply Reservoir Volume (Gigalitre)')
    axs[0].set_xlabel('Date (day)')
    axs[0].legend(volumes.columns)
nse_vol = 1 - ((volumes['CityWat'] - volumes['WARMS'])**2).mean()/\
                (volumes['WARMS'].sub(volumes['WARMS'].mean())**2).mean()
print(nse_vol)
#Load historic water quality data
historic_quality_samples_address = os.path.join(repo_address,"data",'thames_downstream_phosphorus.csv')
quality = pd.read_csv(historic_quality_samples_address,sep=',')
quality = quality.set_index('date')
quality.index = pd.to_datetime(quality.index).date

#Compare phosphorus
for color, (idx, qual) in zip(['r','b'],quality.groupby('id')):
    axs[1].scatter(qual.result,normal_model_results.loc[qual.index,'phosphorus'],s=40,marker='.',color=color)
    ind = normal_model_results.loc[qual.index,'phosphorus'] > 5
    cc = np.corrcoef(qual.result,normal_model_results.loc[qual.index,'phosphorus'])
    print(idx + ' outliers :' + str(cc))
    qual = qual.loc[~ind]
    cc = np.corrcoef(qual.result,normal_model_results.loc[qual.index,'phosphorus'])
    print(idx + ' outliers removed :' + str(cc))
x = np.linspace(*axs[1].get_xlim())
axs[1].plot(x, x,ls=':',color='k',lw=1)
axs[1].legend(['x=y','Sample Site 1','Sample Site 2'])
axs[1].set_xlabel('Sampled Phosphorus (mg/l)')

f.savefig(os.path.join(output_address,"historic_comparison.png"),dpi=900)

#Plot untreated effluent against precipitation and reservoir volume
ind = (normal_model_results.precipitation > 10) & (normal_model_results.reservoir_volume > 192807)

f, ax = plt.subplots(2,1,figsize=(4.6,7))
ax[0].scatter(normal_model_results.precipitation,normal_model_results.untreated_effluent_conc,facecolor='black',s=1.5,marker='.')
#ax[0].set_xlabel('precipitation')
#ax[0].set_ylabel('untreated_effluent_conc')

ax[1].scatter((normal_model_results.reservoir_volume + normal_model_results.service_reservoir_volumes)/1000,normal_model_results.untreated_effluent_conc,facecolor='black',s=1.5,marker='.')
#ax[1].set_xlabel('volume')
#ax[1].set_ylabel('untreated_effluent_conc')

f.savefig(os.path.join(output_address,"precip_vol.png"),dpi=900)
ax[0].scatter(normal_model_results.loc[ind].precipitation,normal_model_results.loc[ind].untreated_effluent_conc,facecolor='red',s=1.5,marker='.')
ax[1].scatter((normal_model_results.loc[ind].reservoir_volume + normal_model_results.loc[ind].service_reservoir_volumes)/1000,normal_model_results.loc[ind].untreated_effluent_conc,facecolor='red',s=1.5,marker='.')
f.savefig(os.path.join(output_address,"precip_vol_hilite.png"),dpi=900)

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
f.savefig(os.path.join(output_address, "water_quality_framing.png"),dpi=900)


f, ax = plt.subplots(2,2,figsize=(4.6*2,7))
l=0
for var in ['phosphorus','untreated_effluent_conc','reservoir_','restrictions']:
   ax[int(l/2),l%2].scatter(normal_model_results[var],supply_only_model_results[var],facecolor='black',s=1.5,marker='.')
   ax[int(l/2),l%2].scatter(normal_model_results[var],wastewater_model_results[var],facecolor='red',s=1.5,marker='.')
   maxo = normal_model_results[var].max()
   ax[int(l/2),l%2].plot([0,maxo],[0,maxo],ls=':')
   l+=1
   
   
ax[0].scatter(normal_model_results.precipitation,normal_model_results.untreated_effluent_conc,facecolor='black',s=1.5,marker='.')

plt.scatter(normal_model_results.phosphorus,supply_only_model_results.phosphorus,'r')
plt.scatter(normal_model_results.phosphorus,wastewater_model_results.phosphorus)


#Abstraction effluent dilution
aed_model = models.model(addresses)
aed_model.add_option(['nopump_rule'])
aed_model_results = aed_model.run(fast=True)
aed_model_results['reservoir_volume'] = aed_model_results['reservoir_volume'].div(1000)
normal_model_results['reservoir_volume'] = normal_model_results['reservoir_volume'].div(1000)

f = misc.aed_plots([normal_model_results,
                 aed_model_results],ind=volumes.index,color=['r','b'],lw=[0.3,0.3,0.3,0.3],ls = ['-','-'], plot_order= [1,1,0,0])
f.savefig(os.path.join(output_address, "abstraction_effluent_dilution.png"),dpi=900)

f, ax = plt.subplots(2,1,figsize=(4.6,7))
l=0
for var in ['phosphorus','reservoir_volume']:
   ax[l].scatter(normal_model_results[var],aed_model_results[var],facecolor='black',s=1.5,marker='.')
   maxo = normal_model_results[var].max()
   ax[l].plot([0,maxo],[0,maxo],ls='--',color='r')
   ax[l].set_aspect('equal', 'box')
   ax[l].set_xlabel(var)
#   ax[l].set_ylim(ax[l].get_xlim())
   l+=1
#f.tight_layout()   
f.savefig(os.path.join(output_address, "AED_scatter.png"),dpi=900)

aed_model_results['reservoir_volume'] *= 1000
normal_model_results['reservoir_volume'] *= 1000
mean_vol = aed_model_results['reservoir_volume'].mean() - normal_model_results['reservoir_volume'].mean()
print('vol diff : ' + str(mean_vol))

#days estimate
for level in range(1,5):
    n_jmo = sum(aed_model_results.restrictions == level)
    n_normal = sum(normal_model_results.restrictions == level)
    print('Level ' + str(level) + ', JMO - normal: ' + str(n_jmo - n_normal))

#Work out stormwater storage increase equivalent
storm_model = models.model(addresses)
inc = 1.11
storm_model.parameters['wastewater_temporary_storage_capacity'] *= inc
storm_model_results = storm_model.run(fast = True)
storm_mean = storm_model_results.untreated_effluent_conc.mean()

print('AED spill ' + str(aed_model_results.untreated_effluent_conc.mean()))
print('Stormwater spill ' + str(storm_mean))
print('(Given the above two numbers are about the same)')
print('Infrastructure equivalent = ' + str(normal_model.parameters['wastewater_temporary_storage_capacity']*(inc-1)))

storm_model = models.model(addresses)
inc = 1.29
storm_model.parameters['wastewater_temporary_storage_capacity'] *= 1.29
storm_model_results = storm_model.run(fast = True)
storm_mean = storm_model_results.untreated_effluent_conc.mean()

print('Wastewater only spill ' + str(wastewater_model_results.untreated_effluent_conc.mean()))
print('Stormwater spill ' + str(storm_mean))
print('(Given the above two numbers are about the same)')
print('Infrastructure equivalent = ' + str(normal_model.parameters['wastewater_temporary_storage_capacity']*(inc-1)))

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
subset.loc['reservoir_volume'] /= 1000
f = misc.colorgrid_plot(-subset.copy())
f.savefig(os.path.join(output_address, "colorgrid_results.png"),dpi=900)

