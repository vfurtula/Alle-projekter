#include <math.h>
#include <LiquidCrystal.h>

// initialize the library with the numbers of the interface pins
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

// Thermocopule data (type B) 
// Source: http://www.omega.com/temperature/z/pdf/z212-213.pdf
// Voltage in microvolts, temperature in C
float temps[]={62.0, 72.0, 82.0, 92.0, 102.0, 112.0, 122.0, 132.0, 142.0, 152.0, 162.0, 172.0, 182.0, 192.0, 202.0, 212.0, 222.0, 232.0, 242.0, 252.0, 262.0, 272.0, 282.0, 292.0, 302.0, 312.0, 322.0, 332.0, 342.0, 352.0, 362.0, 372.0, 382.0, 392.0, 402.0, 412.0, 422.0, 432.0, 442.0, 452.0, 462.0, 472.0, 482.0, 492.0, 502.0, 512.0, 522.0, 532.0, 542.0, 552.0, 562.0, 572.0, 582.0, 592.0, 602.0, 612.0, 622.0, 632.0, 642.0, 652.0, 662.0, 672.0, 682.0, 692.0, 702.0, 712.0, 722.0, 732.0, 742.0, 752.0, 762.0, 772.0, 782.0, 792.0, 802.0, 812.0, 822.0, 832.0, 842.0, 852.0, 862.0, 872.0, 882.0, 892.0, 902.0, 912.0, 922.0, 932.0, 942.0, 952.0, 962.0, 972.0, 982.0, 992.0, 1002.0, 1012.0, 1022.0, 1032.0, 1042.0, 1052.0, 1062.0, 1072.0, 1082.0, 1092.0, 1102.0, 1112.0, 1122.0, 1132.0, 1142.0, 1152.0, 1162.0, 1172.0, 1182.0, 1192.0, 1202.0, 1212.0, 1222.0, 1232.0, 1242.0, 1252.0, 1262.0, 1272.0, 1282.0, 1292.0, 1302.0, 1312.0, 1322.0, 1332.0, 1342.0, 1352.0, 1362.0, 1372.0, 1382.0, 1392.0, 1402.0, 1412.0, 1422.0, 1432.0, 1442.0, 1452.0, 1462.0, 1472.0, 1482.0, 1492.0, 1502.0, 1512.0, 1522.0, 1532.0, 1542.0, 1552.0, 1562.0, 1572.0, 1582.0, 1592.0, 1602.0, 1612.0, 1622.0, 1632.0, 1642.0, 1652.0, 1662.0, 1672.0, 1682.0, 1692.0, 1702.0, 1712.0, 1722.0, 1732.0, 1742.0, 1752.0, 1762.0, 1772.0, 1782.0, 1792.0, 1802.0, 1812.0, 1822.0, 1832.0};
float muvolts[]={0.0, 2.0, 6.0, 11.0, 17.0, 25.0, 33.0, 43.0, 53.0, 65.0, 78.0, 92.0, 107.0, 123.0, 141.0, 159.0, 178.0, 199.0, 220.0, 243.0, 267.0, 291.0, 317.0, 344.0, 372.0, 401.0, 431.0, 462.0, 494.0, 527.0, 561.0, 596.0, 632.0, 669.0, 707.0, 746.0, 787.0, 828.0, 870.0, 913.0, 957.0, 1002.0, 1048.0, 1095.0, 1143.0, 1192.0, 1242.0, 1293.0, 1344.0, 1397.0, 1451.0, 1505.0, 1561.0, 1617.0, 1675.0, 1733.0, 1792.0, 1852.0, 1913.0, 1975.0, 2037.0, 2101.0, 2165.0, 2230.0, 2296.0, 2363.0, 2431.0, 2499.0, 2569.0, 2639.0, 2710.0, 2782.0, 2854.0, 2928.0, 3002.0, 3078.0, 3154.0, 3230.0, 3308.0, 3386.0, 3466.0, 3546.0, 3626.0, 3708.0, 3790.0, 3873.0, 3957.0, 4041.0, 4127.0, 4213.0, 4299.0, 4387.0, 4475.0, 4564.0, 4653.0, 4743.0, 4834.0, 4926.0, 5018.0, 5111.0, 5205.0, 5299.0, 5394.0, 5489.0, 5585.0, 5682.0, 5780.0, 5878.0, 5976.0, 6075.0, 6175.0, 6276.0, 6377.0, 6478.0, 6580.0, 6683.0, 6786.0, 6890.0, 6995.0, 7100.0, 7205.0, 7311.0, 7417.0, 7524.0, 7632.0, 7740.0, 7848.0, 7957.0, 8066.0, 8176.0, 8286.0, 8397.0, 8508.0, 8620.0, 8731.0, 8844.0, 8956.0, 9069.0, 9182.0, 9296.0, 9410.0, 9524.0, 9639.0, 9753.0, 9868.0, 9984.0, 10099.0, 10215.0, 10331.0, 10447.0, 10563.0, 10679.0, 10796.0, 10913.0, 11029.0, 11146.0, 11263.0, 11380.0, 11497.0, 11614.0, 11731.0, 11848.0, 11965.0, 12082.0, 12199.0, 12316.0, 12433.0, 12549.0, 12666.0, 12782.0, 12898.0, 13014.0, 13130.0, 13246.0, 13361.0, 13476.0, 13591.0, 13706.0};

// Calibration data for the Arduino Mega2560 and the amplifier, voltage in millivolts
float ard_volts[]={0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.1, 15.2, 15.3, 15.4, 15.5};	
int ard_bits[]={0.0, 0.0, 3.0, 10.0, 16.0, 23.0, 30.0, 36.0, 43.0, 49.0, 56.0, 63.0, 69.0, 122.0, 189.0, 255.0, 322.0, 388.0, 454.0, 520.0, 587.0, 654.0, 687.0, 720.0, 753.0, 786.0, 820.0, 853.0, 886.0, 919.0, 953.0, 986.0, 992.0, 999.0, 1006.0, 1013.0, 1019.0};

//float ard_volts[]={0.00, 0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 1.05, 1.08, 1.09, 1.10, 1.107};	
//int ard_bits[]={0, 41, 134, 227, 320, 413, 506, 598, 691, 784, 877, 970, 998, 1007, 1016, 1023};

byte temp[8] = {
  B00111,
  B00101,
  B00111,
};

long taeller, vals[]={};

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
  long val=0, add=0;
  for (int iii=0; iii<200; iii++) {
    add = analogRead(0);
    val = val+add;
  }
  val = val/200;
  //int val = test_bit_Temp_accuracy;
  
  // Convert the bits back to voltage and perform correction
  // Save the corrected voltage into a new variable
  double volts = 0.00;
  long int_muvolts = 0;
  for (int i = 0; i < sizeof(ard_bits)-2; i++) {
    if (val>=ard_bits[i] && val<=ard_bits[i+1]) {
        volts = (val-ard_bits[i])*(ard_volts[i+1]-ard_volts[i])/(ard_bits[i+1]-ard_bits[i])+ard_volts[i];
        // Alternative method
        //volts=map(val,ard_bits[i],ard_bits[i+1],ard_volts[i],ard_volts[i+1]);
        
        // Round and convert tempval to an integer
        int_muvolts = 1e3*volts+0.5;
        break;
      }
  }
  // corr_volt is the voltage in microvolts from the pdf Reference Table
  //int corr_volt = int_muvolts;
  
  // TEST
  // map arduino function TRUNCATES both input numbers and the output
  // use map function with caution
  //float int_muvs=map(12,11.898,1023,0.235,13706);
  //float int_muvs2=(12-11.898)*(13706-0.235)/(1023-11.898)+0.235;
  //Serial.println(String(int_muvs));
  //Serial.println(String(int_muvs2));
  
  // Convert the corrected voltage to a temperature value
  if (int_muvolts>=0 && int_muvolts<=13706) {
    double tempval = 0.00;
    long int_tempval=0;
    for (int ii = 0; ii < sizeof(muvolts)-2; ii++) {
      if (int_muvolts>=muvolts[ii] && int_muvolts<=muvolts[ii+1]) {
        tempval = (int_muvolts-muvolts[ii])*(temps[ii+1]-temps[ii])/(muvolts[ii+1]-muvolts[ii])+temps[ii];
        // Alternative method
        //tempval=map(int_muvolts,muvolts[ii],muvolts[ii+1],temps[ii],temps[ii+1]);
        
        // Round and convert tempval to an integer 
        int_tempval = tempval+0.50;
        break;
      }
    }
    
    // Minimize numbers of clears of the display
    // Only update when there has been change in the 
    // temperature compared to the previous value.
   
    vals[taeller]=int_tempval;
    if (taeller>0) {
      if (vals[taeller-1]!=vals[taeller]){
        lcd.clear();
      }
    }
    taeller++;
    
    // set the cursor to column 0, line 1
    // (note: line 1 is the second row, since counting begins with 0):
    if (tempval>99) {
      lcd.setCursor(0, 0);
      // print the number of seconds since reset:
      lcd.print(int_tempval);
      
      lcd.setCursor(4, 0);
      lcd.write(byte(0));
      lcd.setCursor(5, 0);
      lcd.print("C");
    }
    else {
      lcd.clear();
      lcd.setCursor(0, 0);
      // print the number of seconds since reset:
      lcd.print(int_tempval);
      
      lcd.setCursor(4, 0);
      lcd.write(byte(0));
      lcd.setCursor(5, 0);
      lcd.print("C");
    }
    
    // Print to the serial port
    Serial.print(String(val));
    Serial.print(" ");
    Serial.print(String(int_muvolts));
    Serial.print(" ");
    Serial.println(String(tempval));
   
  }
  else if (int_muvolts<0) {
    // (note: line 1 is the second row, since counting begins with 0):
    lcd.setCursor(0, 0);
    lcd.print("<62 ");
    
    lcd.setCursor(4, 0);
    lcd.write(byte(0));
    lcd.setCursor(5, 0);
    lcd.print("C  ");
    
    // Print to the serial port
    Serial.print(String(val));
    Serial.print(" ");
    Serial.print(String(int_muvolts));
    Serial.print(" ");
    Serial.println("<62");
    
  }
  else if (int_muvolts>13706) {
    // (note: line 1 is the second row, since counting begins with 0):
    lcd.setCursor(0, 0);
    lcd.print(">1832");
    
    lcd.setCursor(5, 0);
    lcd.write(byte(0));
    lcd.setCursor(6, 0);
    lcd.print("C");
    
    // Print to the serial port
    Serial.print(String(val));
    Serial.print(" ");
    Serial.print(String(int_muvolts));
    Serial.print(" ");
    Serial.println(">1832");
    
  }
  else {
  }
  //double test = pow(2.27377e+2,5)*pow(2.27377e+2,-5);
  //Serial.println(String(test));
  delay(500);
  //test_bit_Temp_accuracy++;
}
