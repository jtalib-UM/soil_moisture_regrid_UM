#!/bin/bash

#SBATCH --job-name=ants_regrid
#SBATCH --time=1:0:0
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1

#SBATCH --account=n02-NEX006247
#SBATCH --partition=serial
#SBATCH --qos=serial
#SBATCH --mem=124G

# Script will convert SMC to SM stress. Use ANTS to interpolate (due to treatment of coastlines).
# then convert back into SMC
# activate python package with iris, xarray and xesmf
PATH=/home/n02/n02/jostal/miniconda3/bin:$PATH

# define files - including initial SMC, global model dump file with SMwilt, SMcrit etc.
# outfile for SM stress file and regridded dump file (i.e. SMwilt on new domain).
#
# top selection - defined files that can be changed
# 20190304_smc.pp
# JT's three case studies 20190304_smc.pp, 20220405_smc.pp and 20210411_smc.nc
#
initial_SMC_file='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/20220405_smc.pp'
final_regrid_SMC='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/20220405_smc_regridded_ARCHER.nc'
save_smow_name='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/20220405_smow_regridded.nc'

# files which are processed during calculations
SM_stress_outfile='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/SMstress_out.nc'
SM_stress_regrid='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/SMstress_regrid_out.nc'
ANTS_IN='SMstress_regrid_out.nc'
ANTS_OUT='SMstress_regrid_AFTER_COASTADJ.nc'

# bottom selection - files which shouldnt be changed
glm_SMC_dump_file='/work/y07/shared/umshared/ancil/atmos/n1280e/soil_parameters/hwsd_vg/v3/qrparm.soil' # i.e. contains SMwilt at N1280 res.
land_mask_4p4km='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/qrparm.mask' # land mask at 4.4km (already made in recon)
ANTS_HOME='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/' # DIRECTORY to run ANTS from
ANTS_CONTAINER=/work/y07/shared/umshared/ANTS/latest/ants_latest.sif
CONFIG_FILE='ants.highmem.config' # configuration file
LSM_MASK='qrparm.mask' # 4.4km land mask stored in ANTS_HOME
SM_STRESS_REGRID='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/'$ANTS_OUT 
regridded_dump_file='/work/n02/n02/jostal/ancillaries/EA_4p4km/38p5L80_4p4km/qrparm.soil' # SMwilt and SMcrit at 4.4km - already calculated
snow_file='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/umnsaa_pvera000.nc' # starting snow file from previous simulation
file_for_SM_depths='/work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/umnsaa_pverb000.nc'

#
#run python code which saves SMstress
# take initial SM file and convert to SM stress file using surface attributes from glm
srun --distribution=block:block --hint=nomultithread python /work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/SMC_to_stress.py $initial_SMC_file $glm_SMC_dump_file $SM_stress_outfile $file_for_SM_depths

echo "calculated "$SM_stress_outfile

# run code which provides linear interpolation with resolved coastal adjustment
srun --distribution=block:block --hint=nomultithread python /work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/generate_weights_landsea_gridding.py $SM_stress_outfile $land_mask_4p4km $SM_stress_regrid

# USING ANTS TO PERFORM SPIRAL CIRCLE METHOD
singularity exec --home $ANTS_HOME $ANTS_CONTAINER \
            bin/ancil_coast_adj.py $ANTS_IN \
            --output $ANTS_OUT \
            --target-lsm $LSM_MASK

# finally, convert stress to SMC and perform checks
srun --distribution=block:block --hint=nomultithread python /work/n02/n02/jostal/prescribed_SM_files/initial_MO_SMC_v2/stress_to_SMC.py $SM_STRESS_REGRID $regridded_dump_file $final_regrid_SMC $file_for_SM_depths $snow_file $save_smow_name

echo "calculated "$final_regrid_SMC


