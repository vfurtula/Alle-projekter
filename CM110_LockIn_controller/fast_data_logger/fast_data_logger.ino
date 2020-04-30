
char str1[1];
char str2[2];
char str3[3];
char str4[4];

int noofpts=0;
int wait=0;

void setup()
{ 
  // Open serial communications and wait for port to open:
  Serial.begin(9600);
  //analogReadResolution(12);
  //analogReference(INTERNAL1V1);
  
  /*
  if (Serial.available() > 0) {   // something came across serial
  
  // Option 1
  //int val = Serial.read()-'0';
  
  // Option 2
  // Source: http://www.baldengineer.com/blog/2012/07/30/arduino-multi-digit-integers/
  //char buffer[] = {' ',' ',' '}; // Receive up to 3 bytes
  //while (!Serial.available()); // Wait for characters
  //Serial.readBytesUntil('\n', buffer, 3);
  //int incomingValue = atoi(buffer);
  
  // Option 3
  // Source: http://www.baldengineer.com/blog/2012/07/30/arduino-multi-digit-integers/
  integerValue = 0;         // throw away previous integerValue
  while(1) {            // force into a loop until 'n' is received
    incomingByte = Serial.read();
    if (incomingByte == '\n') break;   // exit the while(1), we're done receiving
    if (incomingByte == -1) continue;  // if no characters are in the buffer read() returns -1
    integerValue *= 10;  // shift left 1 decimal place
    // convert ASCII to integer, add, and shift left 1 decimal place
    integerValue = ((incomingByte - 48) + integerValue);
  }
}
*/
}

void loop()
{
  while (noofpts==0) {
    if (Serial.available() > 0) {   // something came across serial
      int plus = Serial.read();
      if (plus==43) {
        while (!Serial.available());
        noofpts=Serial.read();
      }
    }
  }

  while (wait==0) {
    if (Serial.available() > 0) {   // something came across serial
      int equal = Serial.read();
      if (equal==61) {
        while (!Serial.available());
        wait=Serial.read();
      }
    }
  }

  /* 
  // -------------------------------------------------------------------
  // make a string for assembling the data to log, write to serial port
  dataString = "";
  // read three sensors and append to the string:
  for (int analogPin = 0; analogPin < integerValue; analogPin++) {
    int sensor = analogRead(analogPin);
    dataString += String(sensor);
    if (analogPin < integerValue) {
      dataString += " "; 
    }
  }
  */
  
  // Read the input voltage and convert it to bits
  //int val = analogRead(0);
  
  // Due to the AC noise make an avarage of the amplifier/supply output 
  
  
  long val=0, add=0;
  for (int iii=0; iii<noofpts; iii++) {
    add = analogRead(0);
    val = val+add;
  }
  val = val/noofpts;
 
  Serial.println(val);
  delay(wait*1000);
}








