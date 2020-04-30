##########################
### The OPERATION mode ###
##########################

# The operation mode op_mode can be one of the following:
# absx, relx, absy, rely, xyscan, xscan, yscan, reset.
# It is required to specify op_mode operation.
op_mode = 'absx'

    #####################################
    ### The ABSX/RELX/ABSY/RELY setup ###
    #####################################

# Both axes can be moved independently, first change the operation mode
# to f.ex op_mode = 'relx' and x axis will be moved +1000 steps 
# relatively. 
move_axis = 0

    ######################
    ### The SCAN setup ###
    ######################

# units of x-scan are microns, y-scan units are tenths of a microns
# XY-scan parameters are edited here. All 8 parameters
# must be specified when operation mode is set to op_mode='scan'.
xstart=-3000
xend=3000
xstep=300

ystart=-0
yend=-60000
ystep=-3000

# wait_time can be a float number or an integer
wait_time=0.5
# scan_mode can be xwise, ywise, xsnake or ysnake. xsnake is fastest.
# scan_mode variable is ignored for 1-dimensional scans, 
# i.e. op_mode=xscan or op_mode=yscan.
scan_mode='xsnake'

    #######################
    ### The RESET setup ###
    #######################

# You can choose to reset x or y or both xy. To do reset you need to put
# op_mode='reset' and specify reset_mode, ie. axis 'x', 'y' or 'xy'.
# If the position files it6d_ca2_pos_x.txt and it6d_ca2_pos_y.txt are missing
# then they will be created with this command.
reset_mode='xy'

##################
### STORE data ###
##################

# You can store data in a file in a separate folder named new_folder or
# you can leave new_folder blank to save the data in the current folder.
# If you leave file_name blank the data will be saved anyway in a file 
# called 'data_(time)'.
new_folder='data_folder'
file_name='my_data_'

# LOCK-IN time delay setting:
# Set time delay for auto-measure operation (ASM), see page 6-9 in the manual.
# time delay should be minimum 5 seconds for the lockin model 5210.
asm_delay=5