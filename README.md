# disklavier-parser
For converting MIDI files in the Yamaha Disklavier enhanced MIDI format into text files and back

In the resulting text files, one line represents on note / one pedal event. The lines have the form:  
```note name, pitch, key sensor time (in s), key sensor velocity (0-1023), note on time (in s), note on velocity (0-1023), note off time (in s), note off velocity (0-1023)```  
or in the case a pedal event:  
```pedal name, pedal number (191/194/193), event time (in s), pedal position (0-1023), 0, 0, 0, 0```
