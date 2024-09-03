# code to produce initial SM ancillaries 
# In the METUM, soil moisture content is converted into SM STRESS.
# SM stress is then linearly-interpolated. Then regridded SM STRESS is converted back to SMC.
# After conversion back to SMC, there are additional checks including is SM below 0.1*SMwilt.
import iris
import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import xesmf as xe 
import sys

def find_nearest_index(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx

main_directory = '/gws/nopw/j04/nzplus/3C/task_2/jostal/TJ_idealised_study/MO_SM_start_files/'

SM_stress_infile = sys.argv[1]
land_mask_infile = sys.argv[2]
regridded_SM_stress_outfile = sys.argv[3]

SM_stress_n1280 = xr.open_dataset(SM_stress_infile)["moisture_content_of_soil_layer"]
land_mask_4p4km = xr.DataArray.from_iris(iris.load_cube(land_mask_infile))

# get surface field
SM_stress_n1280_sfc = SM_stress_n1280[0]

# compute non-masked regridder
regridder = xe.Regridder(SM_stress_n1280_sfc, land_mask_4p4km,"bilinear")
SM_regrid = regridder(SM_stress_n1280_sfc)

# find where value is extremely high. greater than 1000.0
# loop through regridder, take max weight until no more np.nans.
# first set weights to be indexed (500000,4)
initial_regridded_weights_reshaped = regridder.weights.data.data.reshape(regridder.weights['out_dim'].shape[0],4)

# loop though field
# loop four times - each time taking next highest weight
# initialise a new regridded_weights field
regridded_weights_reshaped = initial_regridded_weights_reshaped.copy()
for max_i in np.arange(4):
    # flatten SM values
    SM_regrid_flattened = SM_regrid.data.flatten()
    # find points where regridded SM is exceptionally large
    mask_above_1000 = SM_regrid_flattened>1000.0
    print (np.count_nonzero(mask_above_1000))    

    # loop through these points and make maximum value = 1.0
    for gp in np.arange(regridder.weights['out_dim'].shape[0]):
        if mask_above_1000[gp] == True:
            
            regrid_weights = initial_regridded_weights_reshaped[gp]
            # find maximum of attempt, i.e. on second attempt find second maximum
            max_index = find_nearest_index(regrid_weights,np.sort(regrid_weights)[::-1][max_i])
            # only set largest index to 1.0
            new_regrid_weights = np.zeros(4)
            new_regrid_weights[max_index] = 1.0
            regridded_weights_reshaped[gp] = new_regrid_weights
            if gp == 499709:
                print (regrid_weights)
                print (max_index)
                print (new_regrid_weights)
                print (regridded_weights_reshaped[gp])
    # flatten new regridded weights and replace regrider values
    new_regridder_weights = regridded_weights_reshaped.flatten()
    regridder.weights.data.data = new_regridder_weights
    SM_regrid = regridder(SM_stress_n1280_sfc)

# loop through four depths than combine and save
SM_list = []
for depth in np.arange(4):
    SM_list.append(regridder(SM_stress_n1280[depth]))

SM_regridded_4p4km_cadj = xr.concat(SM_list,dim='depth')
SM_regridded_4p4km_cadj.name = 'moisture_content_of_soil_layer'

iris.save(SM_regridded_4p4km_cadj.to_iris(),regridded_SM_stress_outfile)
