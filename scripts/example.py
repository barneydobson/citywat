# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 16:48:00 2020

@author: bdobson
"""

import os
import pandas as pd
from matplotlib import pyplot as plt
import models
import numpy as np

#Data addresses
repo_address = os.path.join("C:\\","Users","bdobson","Documents","GitHub","citywat")

precip_address = os.path.join(repo_address,"data","beckton_rainfall_1900_2018_day_25_km.csv")
flow_address_teddington = os.path.join(repo_address,"data","teddington-gauge-39001-naturalised.csv")
flow_address_lee = os.path.join(repo_address,"data","lee-gauge-38001-naturalised.csv")
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

#Load historic water quality data
historic_quality_samples_address = os.path.join(repo_address,"data",'thames_downstream_phosphorus.csv')
quality = pd.read_csv(historic_quality_samples_address,sep=',')
quality = quality.set_index('date')
quality.index = pd.to_datetime(quality.index).date

#Create and run the combined model
normal_model = models.model(addresses)
normal_model_results = normal_model.run(fast=True)
volumes['CityWat'] = normal_model_results.loc[volumes.index,['reservoir_volume','service_reservoir_volumes']].sum(axis=1)
volumes.div(1000).plot()
plt.ylabel('Supply Reservoir Volume (Gigalitre)')
nse = 1 - ((volumes['WARMS'].sub(volumes['CityWat']))**2).mean()/((volumes['WARMS'].sub(volumes['WARMS'].mean()))**2).mean()
print(nse)

#Compare phosphorus
f, ax = plt.subplots()
for idx, qual in quality.groupby('id'):
    ax.scatter(qual.result,normal_model_results.loc[qual.index,'phosphorus'])
    ind = normal_model_results.loc[qual.index,'phosphorus'] > 5
    cc = np.corrcoef(qual.result,normal_model_results.loc[qual.index,'phosphorus'])
    print(idx + ' outliers :' + str(cc))
    qual = qual.loc[~ind]
    cc = np.corrcoef(qual.result,normal_model_results.loc[qual.index,'phosphorus'])
    print(idx + ' outliers removed :' + str(cc))

x = np.linspace(*ax.get_xlim())
ax.plot(x, x,ls=':',color='k')
ax.legend(['x=y','Sample Site 1','Sample Site 2'])
ax.set_xlabel('Sampled Phosphorus (mg/l)')
ax.set_ylabel('CityWat Modelled Phosphorus (mg/l)')


#Plot some state variables
variables = ['flow','reservoir_volume','restrictions','household_output','treated_effluent','untreated_effluent']
f, axs = plt.subplots(len(variables),1)
for variable, ax in zip(variables,axs):
    ax.plot(normal_model_results[variable])
    ax.set_ylabel(variable)
    
#Try adding an option
new_reservoir_model = models.model(addresses)
new_reservoir_model.add_option('supply_reservoir')
new_reservoir_results = new_reservoir_model.run(fast=True)

#Plot some state variables
variables = ['flow','reservoir_volume','restrictions','household_output','treated_effluent','untreated_effluent']
f, axs = plt.subplots(len(variables),1)
for variable, ax in zip(variables,axs):
    ax.plot(normal_model_results[variable])
    ax.plot(new_reservoir_results[variable])
    ax.set_ylabel(variable)