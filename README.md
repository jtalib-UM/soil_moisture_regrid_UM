# Soil_moisture_regrid_UM
A collection of sbatch and python scripts for regridding soil moisture output from the Met Office Unified Model (UM) on ARCHER. These scripts are focused on working with the Limited Area Model version of the UM. These scripts should support those running high-resolution simulations which are bounded by ERA5. 

# Method to regrid soil moisture
To regrid soil moisture, four scripts are required: 
* REGRID_SMC_FULL.slurm - A slurm submission script which performs all four stages of regridding soil moisture.
* SMC_to_stress.py - A python script which converts soil moisture content at the low-resolution grid (i.e. N1280) to the fine-resolution grid (i.e. 4.4 km).
* generate_weights_landsea_gridding.py - A python script which bilinearly interpolates soil moisture taking into consideration the treatment of water bodies by the UM.
* stress_to_SMC.py - A python script which converts soil moisture stress back into soil moisture content. This final script outputs the regridded soil moisture which can then be used to produce appropriate ancillary files. 



