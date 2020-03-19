# -*- coding: utf-8 -*-
import numpy as np
import matplotlib
from matplotlib import pyplot as plt
import matplotlib as mpl
from numpy.ma import masked_array as ma
import pandas as pd

def water_quality_plots(data,ind,color=None,lw=None,ls=None):
    data = [[df.phosphorus for df in data],
                [df.untreated_effluent_conc for df in data],
                [df.treated_effluent_conc for df in data],
                [df.raw_river_conc for df in data]]
    ncols = 2
    nrows = 4
    figsize = (8.3,6.7)
    f, axs = plt.subplots(nrows,ncols,figsize=figsize)
    for i in range(0,len(data)):
        for j in range(0,len(data[i])):
            ls_ = ls[j]
            if i == 1:
                ls_ = '-'
            axs[i,0].plot(data[i][j],color=color[j],lw=lw[i],ls=ls_)
            axs[i,1].plot(data[i][j].loc[ind],color=color[j],lw=lw[i])
        j=0
#        axs[i,0].set_title(data[i][j].name)
        if i%nrows == nrows - 1:
#            axs[i,0].set_xlabel(data[i][j].index.name)
#            axs[i,0].set_xlabel(data[i][j].index.name)
            flag = 0
        else:
            axs[i,0].set_xticks([])        
            axs[i,1].set_xticks([])        
    return f

def aed_plots(data,ind,color=None,lw=None,ls=None, plot_order = None):
    data = [[df.reservoir_volume for df in data],
                [df.restrictions for df in data],
                [df.phosphorus for df in data],
                [df.untreated_effluent_conc for df in data]]
    ncols = 2
    nrows = 4
    figsize = (8.3,6.7)
    f, axs = plt.subplots(nrows,ncols,figsize=figsize)
    for i in range(0,len(data)):
        if plot_order[i] == 0:
            order = range(0,len(data[i]))
        else:
            order = range(len(data[i])-1,-1,-1)
        for j in order:
            ls_ = ls[j]
            if (i == 1) | (i == 3):
                ls_ = '-'
            axs[i,0].plot(data[i][j],color=color[j],lw=lw[i],ls=ls_)
            axs[i,1].plot(data[i][j].loc[ind],color=color[j],lw=lw[i])
                
        j=0
#        axs[i,0].set_title(data[i][j].name)
        if i%nrows == nrows - 1:
#            axs[i,0].set_xlabel(data[i][j].index.name)
#            axs[i,0].set_xlabel(data[i][j].index.name)
            flag = 0
        else:
            axs[i,0].set_xticks([])        
            axs[i,1].set_xticks([])

    return f

def shiftedColorMap(cmap, start=0, midpoint=0.5, stop=1.0, name='shiftedcmap'):
    """
    Created on Dec 11 '13 at 19:20
    
    @author: Paul H
    Source: https://stackoverflow.com/questions/7404116/defining-the-midpoint-of-a-colormap-in-matplotlib
    """

    '''
    Function to offset the "center" of a colormap. Useful for
    data with a negative min and positive max and you want the
    middle of the colormap's dynamic range to be at zero.

    Input
    -----
      cmap : The matplotlib colormap to be altered
      start : Offset from lowest point in the colormap's range.
          Defaults to 0.0 (no lower offset). Should be between
          0.0 and `midpoint`.
      midpoint : The new center of the colormap. Defaults to 
          0.5 (no shift). Should be between 0.0 and 1.0. In
          general, this should be  1 - vmax / (vmax + abs(vmin))
          For example if your data range from -15.0 to +5.0 and
          you want the center of the colormap at 0.0, `midpoint`
          should be set to  1 - 5/(5 + 15)) or 0.75
      stop : Offset from highest point in the colormap's range.
          Defaults to 1.0 (no upper offset). Should be between
          `midpoint` and 1.0.
    '''
    cdict = {
        'red': [],
        'green': [],
        'blue': [],
        'alpha': []
    }

    # regular index to compute the colors
    reg_index = np.linspace(start, stop, 257)

    # shifted index to match the data
    shift_index = np.hstack([
        np.linspace(0.0, midpoint, 128, endpoint=False), 
        np.linspace(midpoint, 1.0, 129, endpoint=True)
    ])

    for ri, si in zip(reg_index, shift_index):
        r, g, b, a = cmap(ri)

        cdict['red'].append((si, r, r))
        cdict['green'].append((si, g, g))
        cdict['blue'].append((si, b, b))
        cdict['alpha'].append((si, a, a))

    newcmap = matplotlib.colors.LinearSegmentedColormap(name, cdict)
    plt.register_cmap(cmap=newcmap)

    return newcmap

def colorgrid_plot(means):
    #Create grid spacing
    pad_col_grid_after = [1,5]
    pad_row_grid_after = [2]
    pad_size = 0.2
    normal_size = 1
    
    def pad_spacing(no, pad_size, normal_size, gaps):
        count = 0
        spacing = [0]
        for x in range(1,no+1):
            count += normal_size
            spacing.append(count)
            if x in gaps:
                count += pad_size
                spacing.append(count)
        return spacing
    
    x_spacing = pad_spacing(len(means.columns), pad_size, normal_size, pad_col_grid_after)
    y_spacing = pad_spacing(len(means.index), pad_size, normal_size, pad_row_grid_after)
    x_spacing_mgrid,y_spacing_mgrid = np.meshgrid(x_spacing,y_spacing)
    
    #insert dummy columns/rows
    l=0
    for x in pad_col_grid_after:
        means.insert(x+l,'dummy-' + str(l),np.NaN)
        l+=1
    none_row = pd.DataFrame(means.iloc[0,:].copy()).T
    none_row[:] = np.NaN
    none_row.index = ['dummy-row']
    l=0
    for x in pad_row_grid_after:
        means = pd.concat([means.iloc[0:(x+l)],none_row,means.iloc[(x+l):]],axis=0,sort = False)
        l+=1
    
    #Create figure spacing
    f2 = plt.figure(figsize=(10.25,5.25))
    grid = plt.GridSpec(len(means.index), len(means.columns) + 1, figure = f2)
    axs2=[]
    axs2.append(plt.subplot(grid[0:len(means.index),0:(len(means.columns))]))
    
    l = 0
    
    #Iterate over variables of interest
    for idx, row in means.iterrows():
        #Create a masked array of the variable of interest
        bool_mask = np.array(np.ones(means.shape),dtype=bool)
        bool_mask[l] = np.array(np.zeros(means.shape[1]),dtype=bool)
        bool_mask[means.isna()] = False
        means_masked = ma(means.values,bool_mask)
        
        #Pick colormaps depending on whether negative is good or bad
        if idx in ['reservoir_volume','raw_river_conc']:
            cmap = mpl.cm.PiYG
        else:
            cmap = mpl.cm.PiYG_r
        
        #Shift the colormap to set the neutral colour to 0
        shifted_cmap = shiftedColorMap(cmap,
                                            start=(1-0.5-abs(min(means.values[l]))/max(abs(max(means.values[l])),abs(min(means.values[l])))/2),
                                            stop=(0.5+abs(max(means.values[l]))/max(abs(max(means.values[l])),abs(min(means.values[l])))/2),
                                            name='shifted')
        
        #Plot color grid
        pm = axs2[0].pcolormesh(x_spacing_mgrid,y_spacing_mgrid,means_masked,linewidth=4,edgecolors='w',cmap=shifted_cmap)
        if idx != 'dummy-row':
        #Create axis for colorbar
            axs2.append(plt.subplot(grid[len(means.index) - l - 1,len(means.columns)]))
            
            #Create colorbar and set axis invisible
            cb = plt.colorbar(pm,ax=axs2[-1],aspect=10,pad=-10)
            axs2[-1].set_axis_off()
        
        l+=1
        
    #Set ticks and labels
    x_spacing = np.array(x_spacing) + 0.5
    for x in pad_col_grid_after:
        x_spacing = np.delete(x_spacing,x)
        
    y_spacing = np.array(y_spacing) + 0.5
    for y in pad_row_grid_after:
        y_spacing = np.delete(y_spacing,y)
    
    axs2[0].set_xticks(x_spacing[0:-1])
    axs2[0].set_yticks(y_spacing[0:-1])
    axs2[0].set_xticklabels(labels=means.dropna(axis=1,how='all').columns,rotation=45)
    axs2[0].set_yticklabels(labels=means.dropna(axis=0,how='all').index)
    axs2[0].set_aspect(1) #If you want squares (but can screw with the colorbars)
    return f2
