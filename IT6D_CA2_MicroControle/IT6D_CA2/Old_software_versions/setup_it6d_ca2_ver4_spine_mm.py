
##########################
### The OPERATION mode ###
##########################

# The operation mode op_mode can be one of the following:
# abs, rel, xyscan, xscan, yscan, reset.
# You MUST specify op_mode operation.
op_mode = 'xyscan'

##################
### STORE data ###
##################
# You can store data in a separate folder named new_folder or
# you can leave new_folder blank to save the data in the current folder.
# If you leave file_name blank the data will be saved anyway in a file 
# called 'data_(time)'.
new_folder='EK090'
file_name='EK090_1550nm_'

    #####################################
    ### The ABS/REL setup ###
    #####################################

# Both axes can be moved simultaniosly or individually, to move only x-axis 
# first change the operation mode to f.ex op_mode='rel' and move_mm=[1,0] 
# then only x-axis will move +1 mm. 
move_mm =[0,0]

    ######################
    ### The SCAN setup ###
    ######################

# XY-scan parameters are lists of 3 inputs in MILLIMETRES: 
# ie. x_scan_mm=[x_start_mm, x_end_mm, x_step_mm]
# In the operation mode op_mode='xyscan' both x_scan_mm and y_scan_mm
# must be specified.
x_scan_mm=[-1,0,0.5]
y_scan_mm=[0.1,0,-0.05]

# wait_time is the dwell time between scaning points.
# wait_time can be a float number or an integer.
wait_time=2

# scan_mode can be xwise, ywise, xsnake or ysnake, where 
# xsnake is the fastest option. scan_mode variable is ignored 
# for 1-dimensional scans, i.e. op_mode=xscan or op_mode=yscan.
scan_mode='xsnake'

    #######################
    ### The RESET setup ###
    #######################

# You can choose to reset x or y or both xy. To do reset you need to put
# op_mode='reset' and specify reset_mode, ie. axis 'x', 'y' or 'xy'.
# If the position files it6d_ca2_pos_x.txt and it6d_ca2_pos_y.txt are missing
# then they will be created with this command.
reset_mode='xy'

# LOCK-IN time delay setting:
# Set time delay for auto-measure operation (ASM), see page 6-9 in the manual.
# time delay should be minimum 5 seconds for the lockin model 5210.
asm_delay=5

# LIMIT all movements to a xy_limiter_mm, this will limit movements for 
# all scans, and absolute and relative movements.
xy_limiter_mm=24.1
