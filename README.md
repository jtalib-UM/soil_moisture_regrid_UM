# Soil_moisture_regrid_UM
A collection of sbatch and python scripts for regridding soil moisture output from the Met Office Unified Model (UM) on ARCHER2 HPC facility. These scripts are focused on working with the Limited Area Model version of the UM. These scripts should support those running high-resolution simulations which are bounded by ERA5. 

Why are these scripts needed?

When running regional UM simulations bounded by ERA5, it is inconsistent to initialise with ERA5 soil moisture. Currently, when outside the Met Office, it is non-trivial to initialise a model with UM fine-resolution soil moisture. Our solution has been to source soil moisture from the MetUM operational model, either through running a short low-res. simulation with UM driving data or by accessing UKMO operational files, and then regridding soil moisture ourselves. Our validation that we correctly regrid soil moisture has been comparing regridded soil moisture with initial soil moisture when performing a UKMO-driven simulation.

# Specific processes when regridding soil moisture.
We proceed with the following steps to interpolate soil moisture:
* Soil moisture is converted into a ''moisture stress'' factor using coarse-resolution soil properties.
* Bilinear interpolation is used to statistically downscale moisture stress to the finer resolution grid.
* Moisture stress is converted back to soil moisture using soil properties that have been interpolated to the high-resolution model grid.

The interpolation of ''moisture stress'' instead of soil moisture ensures that plant transpiration remains consistent between the two horizontal grids. In the MetUM, moisture stress ($\beta$, dimensionless) is related to the instantaneous ($\theta$), critical ($\theta_c$) and wilting ($\theta_w$) soil moisture concentrations (m$`^3`$ m$`^{-3}`$):

$$
    1 & \text{for } \theta \geq \theta_c \\
    \frac{\theta - \theta_w}{\theta_c - \theta_w} & \text{for } \theta_w < \theta < \theta_c \\
    0 & \text{for } \theta \leq \theta_w
$$

where $\theta_c$ and $\theta_w$ are thresholds when evapotranspiration becomes soil moisture-limited or non-existent respectively. These soil properties are calculated through inputting sand, silt and clay soil fractions, sourced from version 1.2 of the Harmonized World Soil Database, into a set of pedotransfer functions that compute soil hydraulic conductivity.

In the case of land points on the finer horizontal grid that are interpolated from a combination of land and ocean points, a 100\% weighting on the nearest land point is used \citep{UMDP_S11}. Albeit rare, for fine-resolution land points surrounded by coarse-resolution ocean grid points (e.g. small oceanic islands), the moisture stress value from the nearest land point is taken. Additionally, after converting moisture stress back to soil moisture, interpolated values may be inconsistent with soil parameters. To prevent disparities between soil parameters and initialised soil moisture, we ensure that soil moisture is at least 10\% of the wilting soil moisture concentration ($\theta_w$) and does not exceed saturation \citep{UMDP_S11}. All of the aforementioned steps are consistent with current UKMO practices. We also follow the same procedure to interpolate operational soil moisture before the 12th July 2017 to the current horizontal resolution, i.e. N768 to N1280. We found that it is non-trivial to interpolate soil moisture for high-resolution MetUM simulations. In light of the continued increase in high-resolution MetUM modelling amongst the research community, we have made python code which reconfigures UKMO operational soil moisture freely available at https://github.com/jtalib-UM/soil\textunderscore moisture\textunderscore regrid\textunderscore UM.

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


