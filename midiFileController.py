from disklavierParser import MidiParser

class MidiFileController:
    def __init__(self, parser):
        self.parser = MidiParser
        self.parser = parser

        self.mBytes = [] #bytes of the midi file
        self.midiFile = ""

        self.i = 0 #current index of the byte list
        self.currentTime = 0

        self.midiFormat = 0
        self.numberOfTracks = 0
        self.quarterNoteDivision = 0
        self.tempo = 0
        self.tickLength = 0
        self.trackLength = 0

    def readHeaderChunk(self):
        #first 4 bytes are just "MThd" in ASCII
        self.i += 4
        #the next 4 bytes give the number of following data bytes, always 6
        self.i += 4

        #the next 16 bits give the midi format
        self.midiFormat = convertBytesToNumber(self.mBytes[self.i:self.i+2]) #should by 0
        print("midi format: %s") %self.midiFormat
        self.i += 2
        #the next 16 bits give the number of tracks
        self.numberOfTracks = convertBytesToNumber(self.mBytes[self.i:self.i+2]) #should by 1
        print("number of tracks: %s") %self.numberOfTracks
        self.i += 2
        #the next 16 bits give the division
        self.quarterNoteDivision = convertBytesToNumber(self.mBytes[self.i:self.i+2])
        print("divisions per quarter note: %s") %self.quarterNoteDivision
        self.i += 2

    def readTrackChunks(self):
        if(self.midiFormat > 0):
            print("midi format %s is not yet implemented") %self.midiFormat
            return

        #first 4 bytes are just "MTrk" in ASCII
        self.i += 4
        #the next 4 bytes give the number of following data bytes
        self.trackLength = convertBytesToNumber(self.mBytes[self.i:self.i+4])
        self.i += 4
        print("read track with %s bytes") %self.trackLength

        self.readEventStream(maxIndex = len(self.mBytes))

    def readMetaEvent(self):
        self.i += 1
        status = self.mBytes[self.i]
        self.i += 1

        if status == 81:
            self.readTempoChange()
        elif status == 127:
            #self.i += 1 #the byte with this index defines the length of the event
            dataByteCount = self.mBytes[self.i]
            self.i += 1

            self.parser.processSequencerEvent(self.mBytes[self.i : self.i+dataByteCount], time=self.currentTime)
            self.i += dataByteCount #skip these bytes

    def readSysexEvent(self):
        self.i += 1
        dataByteCount = self.mBytes[self.i]
        self.i += 1

        self.parser.processSysexEvent(self.mBytes[self.i : self.i + dataByteCount], time=self.currentTime)
        self.i += dataByteCount

    def readTempoChange(self):
        if self.mBytes[self.i] == 3: #additional identifier byte
            self.i += 1
            #the next 3 bytes give the number of microseconds in one quarter
            microSecondsInQuarter = convertBytesToNumber(self.mBytes[self.i:self.i+3])
            self.i += 3
            self.tempo = 60000000/microSecondsInQuarter
            self.tickLength = 60.0/(self.tempo * self.quarterNoteDivision)
            print("tempo: %s M.M., ") %self.tempo,
            print("tickLength: %s s") %self.tickLength
            #self.i += 1

    def readEventStream(self, maxIndex):
        while self.i < (maxIndex - 2):
            #timecode: n bytes with MSB=1, followed by one byte with MSB=0
            deltaT = 0
            while (self.mBytes[self.i] > 127): #for all bytes with MSB=1
                deltaT = deltaT * 128 + (self.mBytes[self.i] - 128)
                self.i += 1
            deltaT = deltaT * 128 + self.mBytes[self.i]
            self.i += 1

            if deltaT > 0:
                self.currentTime += (deltaT * self.tickLength)

            #event: one byte with MSB=1, followed by n bytes with MSB=0
            status = self.mBytes[self.i]
            if status < 128:
                self.i += 1
            elif status == 255:
                self.readMetaEvent()
            elif status == 240:
                self.readSysexEvent()
            elif (status >= 192) & (status <224):
                #short event with one data byte
                self.parser.processStandardEvent(status, p = self.mBytes[self.i+1], v=0, time=self.currentTime)
                self.i += 2
            elif self.mBytes[self.i+2] < 128:
                self.parser.processStandardEvent(status, p = self.mBytes[self.i+1], v=self.mBytes[self.i+2], time=self.currentTime)
                self.i += 3




def convertNumberToBytes(number, numberOfBytes=1):
    byteValues = []

    #print("number to convert to bytes: %s") %number
    for i in range(numberOfBytes):
        thisByte = number % 256
        byteValues.append(thisByte)
        number = (number - thisByte) / 256

    byteValues.reverse()
    #print("number as bytes: %s") %byteValues
    return byteValues

def convertBytesToNumber(bytes):
    number = 0
    for thisByte in bytes:
        number = number * 256 + thisByte
    return number