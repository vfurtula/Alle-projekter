#############################
# USER OPTIONS - EDIT START # 
#############################

# film+substrate measurements
loadSubFilmOlis_str = 'ek062-4.asc'
loadSubFilmFTIR_str = 'ek062-4.DPT'

# substrate measurements only
loadSubOlis_str = 'BareSapphire3b.asc'
loadSubFTIR_str = 'sapphire 3 matt.DPT'

# perform interpolation using one of the following two arguments: 
# 'linear' or 'spline'
fit_linear_spline = 'linear'

# here you can edit the min_max text file after reviewing first graph in Get_TM_Tm.py
# first check min and max extremas without editing the min_max text file
# the input argument is either 'yes' or 'no'.
read_min_max_txtfile = 'no'

# here you can edit the d_mean text file (a single value) but first make sure the
# textfile with d_mean value exists. The input argument is either 'yes' or 'no'.
read_d_mean_txtfile = 'no'

# expected deviation in the substrate transmission measurements in decimal (percent/100)
# alternatively leave it blank or '0.0'
Expected_Substrate_Dev = 0.0

# gaussian factor parameters required for extrema point selection
# high gauissian factor = broadband noise filtering
# low gauissian factor = narrowband noise filtering
# as an example 4 gaussian factors means division of the spectrum in 4 parts
gaussian_factors = [6.5, 1.5, 1.0, 0.0]

# the brake points of the spectrum in electronVolts [eV]
# the length of this list should be larger than gaussian_factors by 1
gaussian_borders = [0.495, 0.6, 0.80, 1.6, 3.2]

# calculation of index m1, include following sections
# empty brackets such as [] means all points included
index_m1_sections = [1,1.65]

# Here you can extend the searching range for extremas where 1 period is given by distance
# between two last maxima points (or minima). The extended range is relative to extremas found 
# without applying the carrier function T_alpha.
num_periods = 2
iterations = 2

# extend the number of data points with additional points the strong absorption region 
# to find alpha and k in the strong absorption region
strong_abs_start_eV = 3.3

# set order of the polyfit function that will determine extraploated refractive index points
fit_poly_order = 4

# set accepted ranges of the polyfit function in eV. You can set several ranges, they need to be in
# ascending order
fit_poly_ranges = [0.6, 0.95, 1.5, 2.5]

# pick the folder read_data_folder where raw data is saved
# save the analysis data in the folder save_analysis_folder
# if both variabels are left empty the program will try to read raw data from- and save analysis data 
# in this folder (where the control files are).
read_data_folder = 'data'
filename = 'savetofile'
create_folder = 'savetofolder'
save_analysis_folder = 'save_please'

###########################
# USER OPTIONS - EDIT END # 
###########################
