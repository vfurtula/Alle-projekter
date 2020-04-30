#include <math.h>
#include <LiquidCrystal.h>

// initialize the library with the numbers of the interface pins
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

// NTC thermistors for temp measurement-B57861S

float temps[]={-55.0, -50.0, -45.0, -40.0, -35.0, -30.0, -25.0, -20.0, -15.0, -10.0, -5.0, 0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0};
float RR[]={96.30, 67.01, 47.17, 33.65, 24.26, 17.70, 13.04, 9.707, 7.293, 5.533, 4.232, 3.265, 2.539, 1.99, 1.571, 1.249, 1.0000, 0.8057, 0.6531, 0.5327, 0.4369, 0.3603, 0.2986, 0.2488, 0.2083, 0.1752, 0.1481, 0.1258, 0.1072, 0.09177, 0.07885, 0.068, 0.05886, 0.05112, 0.04454, 0.03893, 0.03417, 0.03009, 0.02654, 0.02348, 0.02083, 0.01853, 0.01653};

// Calibration data for the Arduino Mega2560 and the amplifier, voltage in millivolts
//float ard_volts[]={0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.1, 15.2, 15.3, 15.4, 15.5};	
//int ard_bits[]={0, 0, 3, 10, 16, 23, 30, 36, 43, 49, 56, 63, 69, 122, 189, 255, 322, 388, 454, 520, 587, 654, 687, 720, 753, 786, 820, 853, 886, 919, 953, 986, 992, 999, 1006, 1013, 1019};

// Calibration data for the Arduino Mega2560 and the amplifier, voltage in millivolts
//float ard_volts[]={0.00, 0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 1.05, 1.08, 1.09, 1.10, 1.107};  
//int ard_bits[]={0, 41, 134, 227, 320, 413, 506, 598, 691, 784, 877, 970, 998, 1007, 1016, 1023};

byte temp[8] = {
  B00111,
  B00101,
  B00111,
};

int i, analog0;
float RR_float, tempval;
long taeller, RR_long, vals[]={};


//int test_bit_Temp_accuracy=0;

// converts bits into voltage
// KNICK precision voltage-supply used with Arduino Mega2560 (analogRef=1.1V)
// Third (3) order approximation
//double Ard_coefs[]={2.56892466e+03, 1.09678885e+03, -3.57156328e-02, 1.88101154e-05};

void setup() {
  // set up the LCD's number of columns and rows:
  lcd.createChar(0, temp);
  lcd.begin(8, 2);  
   
  // Open serial communications and wait for port to open:
  Serial.begin(9600);
  //analogReference(INTERNAL1V1);

}

void loop() {  
  // Read the input voltage and convert it to bits
  // Due to the AC noise make an avarage of the amplifier/supply output 
  /*
  int add;
  long analog0=0;
  for (i=0; i<10; i++) {
    add = analogRead(0);
    analog0 = analog0+add;
  }
  analog0 = analog0/10;
  */
  analog0 = analogRead(0);
  // Convert the corrected voltage to a temperature value
  RR_float = 1023.0/(float)analog0-1.0;
  //Serial.println(String(RR_float));
  //RR_long = (long)RR_float;
  //Serial.println(String(RR_long));
  
  /*
  for (int ii = 0; ii < sizeof(ard_bits)-2; ii++) {
    if (val>=ard_bits[ii] && val<=ard_bits[ii+1]) {
      //tempval = (val-ard_bits[ii])*(ard_volts[ii+1]-ard_volts[ii])/(ard_bits[ii+1]-ard_bits[ii])+ard_volts[ii];
      // Alternative method
      volts=map(val,ard_bits[ii],ard_bits[ii+1],ard_volts[ii],ard_volts[ii+1]);
      int_RR = 1.0/(5.0/volts-1.0);
      Serial.println(String(ard_bits[ii+1]));
      break;
    }
  }
  */
  
  // Convert the corrected voltage to a temperature value
  for (i = 0; i < sizeof(RR)-2; i++) {
    if (RR_float>RR[i]) {
      tempval = (RR_float-RR[i])*(temps[i+1]-temps[i])/(RR[i+1]-RR[i])+temps[i];
      // Alternative method
      //tempval=map(RR_float,RR[i],RR[i+1],temps[i],temps[i+1]);
      //Serial.println(String(RR[i]));
      break;
    }
  }
  
  // Minimize numbers of clears of the display
  // Only update when there has been change in the 
  // temperature compared to the previous value.
 
  vals[taeller]=tempval;
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
  lcd.print(tempval);
  
  lcd.setCursor(5, 0);
  lcd.write(byte(0));
  lcd.setCursor(6, 0);
  lcd.print("C");
  
  // Print to the serial port
  Serial.print(String(analog0));
  Serial.print(" ");
  Serial.print(String(RR_float));
  Serial.print(" ");
  Serial.println(String(tempval));

  //double test = pow(2.27377e+2,5)*pow(2.27377e+2,-5);
  //Serial.println(String(test));
  delay(500);
  //test_bit_Temp_accuracy++;
}
