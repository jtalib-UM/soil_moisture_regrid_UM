# Soil_moisture_regrid_UM
A collection of sbatch and python scripts for regridding soil moisture output from the Met Office Unified Model (UM) on ARCHER2 HPC facility. These scripts are focused on working with the Limited Area Model version of the UM. These scripts should support those running high-resolution simulations which are bounded by ERA5. 

# Needed scripts to regrid soil moisture
To regrid soil moisture, four scripts are required: 
* REGRID_SMC_FULL.slurm - A slurm submission script which performs all four stages of regridding soil moisture.
* SMC_to_stress.py - A python script which converts soil moisture content (SMC) on the low-resolution grid (i.e. N1280) to the fine-resolution grid (i.e. 4.4 km).
* generate_weights_landsea_gridding.py - A python script which bilinearly interpolates soil moisture taking into consideration the treatment of water bodies by the UM.
* stress_to_SMC.py - A python script which converts soil moisture stress back into soil moisture content. This final script outputs the regridded soil moisture which can then be used to produce appropriate ancillary files.

Additionally, you will need to download ancillary tools. These can either be downloaded from here (```bin``` folder) or extracted straight from the Met Office code repository:

```bash
svn checkout --username <username> https://code.metoffice.gov.uk/svn/ancil/ants/tags/0.19.0/bin/
```

Replace <username> with your Met Office user account name, and enter your password when it is requested. This version may be out of date at time of access.

# Method to regrid soil moisture
REGRID_SMC_FULL.slurm is the overarching script that will submit a job which inputs all the appropriate files and regrids soil moisture content.  
Tasks which need to be completed for this file to successfully run are:
1. In line 8, you need to put in your ARCHER account.
2. *initial_SMC* (line 23) - The filename to the SMC file on the original grid that you wish to regrid.
3. *SM_stress_outfile* (line 25) - Outputting soil moisture stress outfile. This will be soil moisture stress on the low-res. grid.
4. *file_for_SM_depths* (line 26) - Refers to an output file with all four soil moisture layer depths. From this, the layer depths are extracted.
5. *land_mask* (line 34) - The fine-resolution land mask.
6. *SM_stress_regrid* (line 35) - Filename for regridded soil moisture stress file.
7. *SM_STRESS_REGRID* (line 45) - Filename for regridded soil moisture stress after coastal adjusting achieved using ANTS.   
8. *regridded_soil_properties* (line 59) - Soil properties on the fine-resolution grid (this should have already been computed when running creating initial ancillary files). 
9. *final_regrid_SMC* (line 60) - Final output file with regridded soil moisture content!
10. *snow_file* (line 61) - A file with snow output. This is sometimes needed when creating SMC ancillary with xancil.
11. *save_smow_name* (line 62) - Final output file with both SMC and snow.

# Citation
If this code supports your research please cite *Talib, J., Taylor, C.M., Klein, C., Warner, J., Munday, C., Fowell, S. and Charlton-Perez, C., In Prep. Modelling the influence of soil moisture on the Turkana jet. Quarterly Journal of the Royal Meteorological Society.*

# Contact
These scripts will not be updated regularly. If you have any questions, please feel free to contact Joshua Talib at jostal@ceh.ac.uk.


