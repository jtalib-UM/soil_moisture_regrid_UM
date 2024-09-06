#!/bin/bash

#SBATCH --job-name=ants_regrid
#SBATCH --time=1:0:0
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1

#SBATCH --account= # PUT IN YOUR OWN ARCHER ACCOUNT NUMBER
#SBATCH --partition=serial
#SBATCH --qos=serial
#SBATCH --mem=124G
#
# activate python package with iris, xarray and xesmf
PATH=/home/n02/n02/jostal/miniconda3/bin:$PATH

# There are three main components to this sbatch script:
# (1) Convert soil moisture content (SMC) into soil moisture stress (Best et al., 2011): python script SMC_to_stress.py
# (2) Perform bilinear interpolation with coastal adjustments (Sharp 2020).
# (3) Convert soil moisture stress back into SMC

# Part (1) Convert SMC into soil moisture stress. #####################################################################################
# First define files.
initial_SMC='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/20220405_smc.pp' # Your initial apart SMC file which you wish to be interpolated.
glm_soil_properties='/work/y07/shared/umshared/ancil/atmos/n1280e/soil_parameters/hwsd_vg/v3/qrparm.soil' # i.e. contains SMwilt etc. at N1280 res.
SM_stress_outfile='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/soil_moisture_regrid_UM/SMstress_out.nc' # outputted soil moisture stress file
file_for_SM_depths='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/umnsaa_pverb000.nc' # a file which contains soil moisture depths

# run python script which convert SMC into SM stress.
srun --distribution=block:block --hint=nomultithread python /work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/soil_moisture_regrid_UM/SMC_to_stress.py $initial_SMC $glm_soil_properties $SM_stress_outfile $file_for_SM_depths

# Part (2) #############################################################################################################################
# run python script which performs linear interpolation with resolved coastal adjustment
# Define files.
land_mask='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/qrparm.mask' # land mask at regional model resolution already created during production of ancillaries.
SM_stress_regrid='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/soil_moisture_regrid_UM/SMstress_regrid_out.nc' # this file will be SM stress regridded to the finer resolution.
# additional files for coastal adjustment performed by ANTS (for grid points fully surronded by ocean [small islands/vary rare].)
ANTS_IN='SMstress_regrid_out.nc'
ANTS_OUT='SMstress_regrid_AFTER_COASTADJ.nc'

# bottom selection - files which shouldnt be changed
ANTS_HOME='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/soil_moisture_regrid_UM/' # DIRECTORY to run ANTS from
ANTS_CONTAINER=/work/y07/shared/umshared/ANTS/latest/ants_latest.sif
CONFIG_FILE='ants.highmem.config' # configuration file
LSM_MASK='qrparm.mask' # 4.4km land mask stored in ANTS_HOME
SM_STRESS_REGRID='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/soil_moisture_regrid_UM/'$ANTS_OUT

# run python script
srun --distribution=block:block --hint=nomultithread python /work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/soil_moisture_regrid_UM/generate_weights_landsea_gridding.py $SM_stress_outfile $land_mask $SM_stress_regrid

# USING ANTS TO PERFORM SPIRAL CIRCLE METHOD
singularity exec --home $ANTS_HOME $ANTS_CONTAINER \
            bin/ancil_coast_adj.py $ANTS_IN \
            --output $ANTS_OUT \
            --target-lsm $LSM_MASK

# At this point, you will have a file called SMstress_regrid_AFTER_COASTADJ.nc. 
# Part (3) ###############################################################################################################################
# Convert from SM stress at fine resolution to SMC.
regridded_soil_properties='/work/n02/n02/jostal/ancillaries/EA_4p4km/38p5L80_4p4km/qrparm.soil' # soil properties at the finer resolution
final_regrid_SMC='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/soil_moisture_regrid_UM/20220405_smc_regridded_ARCHER.nc'
snow_file='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/umnsaa_pvera000.nc' # starting snow file from previous simulation
save_smow_name='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/soil_moisture_regrid_UM/20220405_smow_regridded.nc' # script also produces netcdf file which contains SMC and snow - may be necessary when producing anciallary file using xancil.

srun --distribution=block:block --hint=nomultithread python /work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/soil_moisture_regrid_UM/stress_to_SMC.py $SM_STRESS_REGRID $regridded_soil_properties $final_regrid_SMC $file_for_SM_depths $snow_file $save_smow_name

echo "calculated "$final_regrid_SMC


