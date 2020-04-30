import sys, serial, argparse, time, re
import numpy as np
import matplotlib.pyplot as plt 

class Zaber_Tmca:
	def __init__(self,my_serial):
	  # activate the serial. CHECK the serial port name!
	  self.my_serial=my_serial
	  self.ser = serial.Serial(self.my_serial, 9600)
	  print "Zaber serial port:", self.my_serial

	# convert a single value to 4 bytes
	def defBytes(self,Cmd_data):
	  if Cmd_data<0:
	    Cmd_data=256**4+Cmd_data
	  else:
	    pass
	  Cmd_bytes=[]
	  Cmd_data_=Cmd_data
	  for i in range(4)[::-1]:
	    Cmd_bytes.extend([Cmd_data_/256**i])
	    Cmd_data_=Cmd_data_-256**i*Cmd_bytes[-1]
	    
	  return Cmd_bytes[::-1]

	# read from the serial
	def readBytes(self):
	  data=self.ser.read(6)
	  data_ord=[ord(val) for val in data]
	  if(len(data_ord) == 6): # expected no. of bytes from serial
	    Rpl_Byte_6=data_ord[5]
	    Rpl_Byte_5=data_ord[4]
	    Rpl_Byte_4=data_ord[3]
	    Rpl_Byte_3=data_ord[2]
	  else:
	    raise ValueError("Exactely 6 bytes required!")
	  Reply_Data = 256**3*Rpl_Byte_6 + 256**2*Rpl_Byte_5 + 256*Rpl_Byte_4 + Rpl_Byte_3
	  if Rpl_Byte_6>127:
	    Reply_Data = Reply_Data-256**4

	  return Reply_Data
  
  ####################################################################
  # Zaber functions
  ####################################################################

	def set_Reset(self):
	  setRes=[1,0]+self.defBytes(0)
	  self.ser.write([chr(tal) for tal in setRes])
	  #print "The stepper is reset!"

	def move_Home(self):
	  moveHome=[1,1]+self.defBytes(0)
	  self.ser.write([chr(tal) for tal in moveHome])
	  final_pos=self.readBytes()
	  #print "Move to home position! Final position:", final_pos
	  return final_pos

	def move_Absolute(self,val):
		try:
		  moveAbsolute=[1,20]+self.defBytes(val)
		  self.ser.write([chr(tal) for tal in moveAbsolute])
		  #print "...moving absolute"
		  final_pos=self.readBytes()
		  #print "Final position:", final_pos
		  return final_pos
		except Exception, e:
			raise ValueError("Input not valid, perhaps it is out of range!")

	def move_Relative(self,val):
		try:
		  moveRelative=[1,21]+self.defBytes(val)
		  #print "...moving relative", val
		  self.ser.write([chr(tal) for tal in moveRelative])
		  final_pos=self.readBytes()
		  ##print "Final position:", final_pos
		  return final_pos
		except Exception, e:
			raise ValueError("Input not valid, perhaps it is out of range!")

	def move_Tracking(self):
	  moveTracking=[1,8]
	  self.ser.write([chr(tal) for tal in moveTracking])
	  pos=self.readBytes()
	  #print pos
	  return pos

	def move_Const_Speed(self,val):
	  moveConSpeed=[1,22]+self.defBytes(val)
	  self.ser.write([chr(tal) for tal in moveConSpeed])
	  speed=self.readBytes()
	  #print "...moving at const speed of", speed
	  return speed

	def set_Home_Speed(self,val):
	  setHomeSpeed=[1,41]+self.defBytes(val)
	  self.ser.write([chr(tal) for tal in setHomeSpeed])
	  speed=self.readBytes()
	  #print "Set home speed:", speed
	  return speed

	def set_Stop(self):
	  setStop=[1,23]+self.defBytes(0)
	  self.ser.write([chr(tal) for tal in setStop])
	  final_pos=self.readBytes()
	  #print "stepper STOP! Final position:", final_pos
	  return final_pos

	def set_Current_Position(self,val):
	  setPos=[1,45]+self.defBytes(val)
	  self.ser.write([chr(tal) for tal in setPos])
	  set_pos=self.readBytes()
	  #print "Set current position:", set_pos
	  return set_pos

	def set_Microstep_Resolution(self,val):
		setResol=[1,37]+self.defBytes(val)
		self.ser.write([chr(tal) for tal in setResol])
		set_resol=self.readBytes()
		#print "Set microstep resolution:", set_resol
		return set_resol

	def set_Maximum_Position(self,val):
	  retPos=[1,44]+self.defBytes(val)
	  self.ser.write([chr(tal) for tal in retPos])
	  max_pos=self.readBytes()
	  #print "Maximum position:", max_pos
	  return max_pos
	
	def return_Current_Position(self):
	  retPos=[1,60]+self.defBytes(0)
	  self.ser.write([chr(tal) for tal in retPos])
	  ret_pos=self.readBytes()
	  #print "Current position:", ret_pos
	  return ret_pos

	def set_Hold_Current(self,val):  
	  setHoldCurr=[1,39]+self.defBytes(val)
	  self.ser.write([chr(tal) for tal in setHoldCurr])
	  input_val=self.readBytes()
	  #print "Set hold current:", input_val/40.0, "Amps"
	  return input_val/40.0

	def set_Running_Current(self,val):  
	  setRunCurr=[1,38]+self.defBytes(val)
	  self.ser.write([chr(tal) for tal in setRunCurr])
	  input_val=self.readBytes()
	  #print "Set running current:", input_val/40.0, "Amps"
	  return input_val/40.0

	def set_Target_Speed(self,val):
	  if val<=0:
	    raise ValueError("Target speed should be grater than 0!")
	  setTarSpeed=[1,42]+self.defBytes(val)
	  self.ser.write([chr(tal) for tal in setTarSpeed])
	  speed=self.readBytes()
	  #print "New target speed:", speed
	  return round(speed*9.375*60/(64*96),2)

	def return_Setting(self,val):
	  retSet=[1,53]+self.defBytes(val)
	  self.ser.write([chr(tal) for tal in retSet])
	  setting=self.readBytes()
	  #print "For cmd", val, "the setting is", setting
	  return setting

	def return_Status(self):
	  retStat=[1,54]+self.defBytes(0)
	  self.ser.write([chr(tal) for tal in retStat])
	  status=self.readBytes()
	  ##print "The status code is", status
	  return status

	def return_Device_Mode(self):
	  retMode=[1,53]+self.defBytes(40)
	  self.ser.write([chr(tal) for tal in retMode])
	  Cmd_mode=self.readBytes()
	  allbytes='{0:016b}'.format(Cmd_mode)
	  #print ''.join(["Get device mode (",str(Cmd_mode),"): ", allbytes[::-1]])
	  return allbytes[::-1], Cmd_mode

	def set_Device_Mode(self,val):
	  setMode=[1,40]+self.defBytes(val)
	  self.ser.write([chr(tal) for tal in setMode])
	  Cmd_mode=self.readBytes()
	  allbytes='{0:016b}'.format(Cmd_mode)
	  #print ''.join(["New device mode (",str(Cmd_mode),"): ", allbytes[::-1]])
	  return allbytes[::-1], Cmd_mode

	# clean up serial
	def close(self):
	  # close serial
	  print "Zaber port flushed and closed"
	  self.ser.flush()
	  self.ser.close() 

def main():
  
  Za = Zaber_Tmca("/dev/ttyUSB0")
  Za.set_Hold_Current(20)
  Za.set_Running_Current(40)
  
  # disable/enable home status
  Za.set_Current_Position(100000)
  
  # disable/enable potentiometer 
  Cmd_bytes, Cmd_mode = Za.return_Device_Mode()
  if Cmd_bytes[3]=='1':
    Za.set_Device_Mode(Cmd_mode-2**3)
  # disable/enable move tracking
  Cmd_bytes, Cmd_mode = Za.return_Device_Mode()
  if Cmd_bytes[4]=='1':
    Za.set_Device_Mode(Cmd_mode-2**4)
  
  Za.move_Const_Speed(5000)
  
  time.sleep(5)
  Za.set_Stop()
  Za.return_Current_Position()
  Za.set_Target_Speed(500)
  Za.move_Relative(-50000)
  '''
  status_code = Za.return_Status()
  while status_code==21:
    Za.move_Tracking()
    status_code = Za.return_Status()
  '''
  Za.return_Current_Position()
  
  
  Za.set_Hold_Current(0)
  
  # clean up
  Za.close()
 
if __name__ == "__main__":
  main()
  


