#include <math.h>
#include <LiquidCrystal.h>

// initialize the library with the numbers of the interface pins
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

// NTC thermistors for temp measurement-B57861S

//float temps[]={-30.0, -25.0, -20.0, -15.0, -10.0, -5.0, 0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0};
//float RR[]={17.70, 13.04, 9.707, 7.293, 5.533, 4.232, 3.265, 2.539, 1.99, 1.571, 1.249, 1.0, 0.8057, 0.6531, 0.5327, 0.4369, 0.3603, 0.2986, 0.2488, 0.2083, 0.1752, 0.1481, 0.1258, 0.1072, 0.09177, 0.07885, 0.068};

long temps[]={-5500000, -5000000, -4500000, -4000000, -3500000,-3000000, -2500000, -2000000, -1500000, -1000000, -500000, 0, 500000, 1000000, 1500000, 2000000, 2500000, 3000000, 3500000, 4000000, 4500000, 5000000, 5500000, 6000000, 6500000, 7000000, 7500000, 8000000, 8500000, 9000000, 9500000, 10000000, 10500000, 11000000, 11500000, 12000000, 12500000, 13000000, 13500000, 14000000, 14500000, 15000000, 15500000};
long RR[]={9630000, 6701000, 4717000, 3365000, 2426000, 1770000, 1304000, 970700, 729300, 553300, 423200, 326500, 253900, 199000, 157100, 124900, 100000, 80570, 65310, 53270, 43690, 36030, 29860, 24880, 20830, 17520, 14810, 12580, 10720, 9177, 7885, 6800, 5886, 5112, 4454, 3893, 3417, 3009, 2654, 2348, 2083, 1853, 1653};

// Calibration data for the Arduino Mega2560 and the amplifier, voltage in millivolts
//float ard_volts[]={0.00, 0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 1.05, 1.08, 1.09, 1.10, 1.107};  
//int ard_bits[]={0, 41, 134, 227, 320, 413, 506, 598, 691, 784, 877, 970, 998, 1007, 1016, 1023};

byte temp[8] = {
  B00111,
  B00101,
  B00111,
};

int i;
float RR_float, temp_float;
long taeller, RR_int, temp_int, analog0, vals[]={};







void setup() {
  // set up the LCD's number of columns and rows:
  lcd.createChar(0, temp);
  lcd.begin(8, 2);  
   
  // Open serial communications and wait for port to open:
  Serial.begin(9600);
  //analogReference(INTERNAL1V1);
  
}






void loop() {
  
  analog0 = analogRead(0);
  // Convert the corrected voltage to a temperature value
  RR_int = 102300000/analog0-100000;
  RR_float = 1023.0/(float)analog0-1.0;
  //Serial.println(String(RR_float));

  for (i = 0; i < sizeof(RR)-2; i++) {
    if (RR_int>=RR[i] && RR_int<=RR[i+1]) {
      temp_int = (RR_int-RR[i])*(temps[i+1]-temps[i])/(RR[i+1]-RR[i])+temps[i];
      //Serial.println(String(temp_int));
      // Alternative method
      //temp_int = map(RR_int,RR[i],RR[i+1],temps[i],temps[i+1]);
      temp_float=(float)temp_int/100000.0;
      //Serial.println(String(temp_float));
      break;
    }
  }
  
  // Minimize numbers of clears of the display
  // Only update when there has been change in the 
  // temperature compared to the previous value.
 
  vals[taeller]=temp_int;
  if (taeller>0) {
    if (vals[taeller-1]!=vals[taeller]){
      lcd.clear();
    }
  }
  taeller++;
  
  // set the cursor to column 0, line 1
  // (note: line 1 is the second row, since counting begins with 0):

  lcd.clear();
  lcd.setCursor(0, 0);
  // print the number of seconds since reset:
  lcd.print(temp_float);
  
  lcd.setCursor(5, 0);
  lcd.write(byte(0));
  lcd.setCursor(6, 0);
  lcd.print("C");
  
  // Print to the serial port
  Serial.print(String(analog0));
  Serial.print(" ");
  Serial.print(String(RR_float));
  Serial.print(" ");
  Serial.println(String(temp_float));

  //double test = pow(2.27377e+2,5)*pow(2.27377e+2,-5);
  //Serial.println(String(test));
  delay(500);
  //test_bit_Temp_accuracy++;

}




