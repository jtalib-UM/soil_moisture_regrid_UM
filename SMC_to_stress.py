import iris
import xarray as xr
import numpy as np
import sys
import xesmf

initial_SMC_filename = sys.argv[1]
glm_dump_filename = sys.argv[2]
SMstress_outfile = sys.argv[3]
glm_start_dump_filename = sys.argv[4]

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

save_directory = '/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/'

rho_water = 997.77

SM_init = iris.load_cube(initial_SMC_filename)
SM_wilt = load_dump_file(glm_dump_filename,'m01s00i040')
SM_crit = load_dump_file(glm_dump_filename,'m01s00i041')
SM_sat = load_dump_file(glm_dump_filename,'m01s00i043')
SM_init_4km = iris.load_cube(glm_start_dump_filename,'moisture_content_of_soil_layer') # for depths

# ensure spatial extent is same as initial SM file - i.e. Warner's domain.
SM_wilt = extract_lat_lon_init_SM_region(SM_wilt,SM_init)
SM_crit = extract_lat_lon_init_SM_region(SM_crit,SM_init)
SM_sat = extract_lat_lon_init_SM_region(SM_sat,SM_init)

# convert to SMC VOLUME and SMC stress.
# copy n1280 initial SM cube
SM_volume = SM_init.copy()
SM_stress = SM_init.copy()

# work out SM depths, i.e. 0.1-0.0, 0.35-0.1
SM_depths = SM_init_4km.coord('depth').bounds[:,1]-SM_init_4km.coord('depth').bounds[:,0]

# loop through each layer. Work out SM volume (SMC/(depth*rho_water)), work out SM stress ((SMV-SMwilt)/(SMcrit-SMwilt))
for depth_i in np.arange(SM_init_4km.coord('depth').shape[0]):
    SM_volume.data[depth_i] = SM_init.data[depth_i]/(SM_depths[depth_i]*rho_water)
    SM_stress.data[depth_i] = (SM_volume.data[depth_i]-SM_wilt.data)/(SM_crit.data-SM_wilt.data)

# save SM stress
iris.save(SM_stress,SMstress_outfile)

