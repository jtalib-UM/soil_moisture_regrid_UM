import iris
import xarray as xr
import numpy as np
import sys

SMstress_filename = sys.argv[1]
regridded_dump_filename = sys.argv[2]
regridded_SMC_outfile = sys.argv[3]
glm_start_dump_filename = sys.argv[4]
snow_file = sys.argv[5]
regridded_smow_outfile = sys.argv[6]

def find_nearest_index(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx

def load_dump_file(dumpfile,stash_code):
    ''' function which loads dump file but changes longitude to -180 to 180'''
    cube = iris.load_cube(dumpfile,stash_code)
    xr_cube = xr.DataArray.from_iris(cube)
    xr_cube = xr_cube.assign_coords(longitude=(((xr_cube.longitude + 180.0) % 360.0) - 180.0))
    xr_cube = xr_cube.sortby([xr_cube.longitude])
    cube = xr_cube.to_iris()
    return cube

def extract_lat_lon_init_SM_region(cube,SM_init_cube):
    return cube.extract(iris.Constraint(latitude=lambda cell: np.min(SM_init_cube.coord('latitude').points) <= cell <= np.max(SM_init_cube.coord('latitude').points))).extract(iris.Constraint(longitude=lambda cell: np.min(SM_init_cube.coord('longitude').points) <= cell <= np.max(SM_init_cube.coord('longitude').points)))

rho_water = 997.77

# convert back to SMC using 4km ancil. Land ancillary created during previous run. May need to be done for other domains and resolution.
SM_wilt_4km = iris.load_cube(regridded_dump_filename,'m01s00i040')
SM_crit_4km = iris.load_cube(regridded_dump_filename,'m01s00i041')
SM_sat_4km = iris.load_cube(regridded_dump_filename,'m01s00i043')
SM_start_4km = iris.load_cube(glm_start_dump_filename,'moisture_content_of_soil_layer') # downloaded for depths

SM_stress_regrid = iris.load_cube(SMstress_filename)

snow = iris.load_cube(snow_file,'m01s00i023')[0] # download snow from previous simulation (essentially all zero) to make xancil file (combines smc and smow together. Also use first timestep

# work out SM depths, i.e. 0.1-0.0, 0.35-0.1
SM_depths = SM_start_4km.coord('depth').bounds[:,1]-SM_start_4km.coord('depth').bounds[:,0]

## convert from SM stress to SM volume
# copy 4km SM stress regridded cube
SM_volume_regrid = SM_stress_regrid.copy()
SM_regrid = SM_stress_regrid.copy()

# work out SM volume - (SMstress*(SMcrit-SMwilt))+SMwilt, then check SMV is below SM_saturation, i.e. model can't be above saturation.
# then convert SM volume to actual SM content (SM = SMvolume*rho_water*SMdepths
for depth_i in np.arange(SM_start_4km.coord('depth').shape[0]):
    SM_volume_regrid.data[depth_i] = SM_stress_regrid.data[depth_i]*(SM_crit_4km.data-SM_wilt_4km.data)+SM_wilt_4km.data
    SM_volume_regrid.data[depth_i] = np.min(np.ma.asarray([SM_volume_regrid.data[depth_i].data,SM_sat_4km.data.data]),axis=0)
    SM_regrid.data[depth_i] = SM_volume_regrid.data[depth_i]*rho_water*SM_depths[depth_i]

##
# Final checks made by UM, in units of soil moisture content
# Is SMC greater than 0.1*SM wilting value
# another check, is SMC less than saturation.
for depth_i in np.arange(SM_start_4km.coord('depth').shape[0]):
    smc_min = 0.1*SM_wilt_4km.data*SM_depths[depth_i]*rho_water
    SM_regrid.data[depth_i] = np.max(np.ma.asarray([smc_min,SM_regrid.data[depth_i].data]),axis=0)
    smc_max = SM_sat_4km.data*SM_depths[depth_i]*rho_water
    SM_regrid.data[depth_i] = np.min(np.ma.asarray([smc_max,SM_regrid.data[depth_i].data]),axis=0)

# at the very end, mask negative value
#SM_regrid.data = np.ma.masked_less(SM_regrid.data,0.0)

#for depth_i in np.arange(SM_stress_regrid.coord('depth').shape[0]):
#    SM_regrid.data[depth_i].mask = SM_wilt_4km.data.mask

# if file contains 'soil_model_level_number' aux coord, need to add a depth coord.
aux_coord_names = []
for coord in SM_stress_regrid.aux_coords:
    aux_coord_names.append(coord.var_name)

if (np.asarray(aux_coord_names) == 'soil_model_level_number').any():
    SM_regrid.add_dim_coord(SM_start_4km.coord('depth'),0)

# mask all negative values in SM_regrid
SM_regrid.data = np.ma.masked_less(SM_regrid.data,0.0)
#SM_regrid.data = np.ma.masked_greater(SM_regrid.data,5000.0)
#SM_regrid.data.fill_value = np.nan
# fill snow with 0.0
#snow.data = snow.data.fill(0.0)

iris.save(SM_regrid,regridded_SMC_outfile,fill_value=SM_regrid.data.fill_value)

smow = iris.cube.CubeList([SM_regrid,snow])
# combine files to create a smow file
iris.save(smow,regridded_smow_outfile,fill_value=SM_regrid.data.fill_value)
