# DO NOT remove help_string variable, it is required in the program
help_string="""
Desrciption of the content in the required config file with the
first 8 arguments required, and the 2 last arguments optional:
Argument  1: Start [nm], type INT, range: 0-9000
Argument  2: Stop [nm], type INT, range: 0-9000
Argument  3: Step [nm], type INT, range: 1-255
Argument  4: Wait-time [sec], type FLOAT, range: 1-100
Argument  5: Avg-pts, type INT, no. of averaging points for Arduino, range: 1-255
Argument  6: Expand, type INT, range: 1-256
Argument  7: Offset, type FLOAT, range: 0-1
Argument  8: Sensitivity, type INT, range: 0-10000
Argument  9: Sensitivity unit, type STRING, sensitivity unit read from lock-in
Argument 10: filename, type STRING, give a filename [optional]
Argument 11: create_folder, type STRING, save data in a subfolder [optional]
................................................................................
To run the config file use following syntax in your terminal:
python Run_CM110_V7.py my_config_file
Do not use .py extension on my_config_file
................................................................................
IMPORTANT!
Do not wipe out ANY of the variable names in the config file, 
unpredicted failure will occur otherwise.
"""
##################################################
########### USER CHANGES IN THIS BLOCK ###########
##################################################
Start=300
Stop=320
Step=1
Wait_time=2
Avg_pts=25
Expand=1
Offset=0
Sensitivity=50
Sens_unit='uV'
filename='many_pts_'
create_folder='ZnS'
##################################################
##################################################
##################################################

# ADDITIONAL INFORMATION
# Equation for analog output in a SR850 Lock-in Amplifier, 
# see page 108 in the manual.
# The X and Y lock-in outputs are always available
# at these connectors (BNC rear side). The bandwidth of these outputs
# is 100 kHz. A full scale input signal will generate plus-minus 10 V
# at these outputs. The output impedance is <1 Ohm
# and the output current is limited to 10 mA.
# These outputs are affected by the X and Y offsets
# and expands. The actual outputs are
# Xout=(X/sensitivity-offset)*expand*10 V
# Yout=(Y/sensitivity-offset)*expand*10 V
