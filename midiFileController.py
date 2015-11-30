from disklavierParser import MidiParser
import os

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
            if status < 128: #this should not occur
                self.i += 1
            elif status == 255: #meta event
                self.readMetaEvent()
            elif status == 240: #sysex event
                self.readSysexEvent()
            elif (status >= 192) & (status <224): #short event with one data byte
                self.parser.processStandardEvent(status, p = self.mBytes[self.i+1], v=0, time=self.currentTime)
                self.i += 2
            elif self.mBytes[self.i+2] < 128: #standard event with two data bytes
                self.parser.processStandardEvent(status, p = self.mBytes[self.i+1], v=self.mBytes[self.i+2], time=self.currentTime)
                self.i += 3
            else:
                self.i += 1


    def writeEventToFile(self, dataBytes, deltaT = 0):
        ticks = 0
        if (deltaT > 0) & (self.tickLength > 0):
            ticks = int((deltaT / self.tickLength) + 0.5) #+0.5 to round correctly

        self.midiFile.write(bytearray(self.convertTicksToMidiDeltaBytes(ticks)))
        self.midiFile.write(bytearray(dataBytes))

    def writeSysexEvent(self, dataBytes, deltaT = 0):
        bytesToWrite = [240, len(dataBytes)]
        bytesToWrite.extend(dataBytes)
        self.writeEventToFile(bytesToWrite, deltaT=deltaT)

    def writeSequencerEvent(self, dataBytes, deltaT = 0):
        bytesToWrite = [255, 127, len(dataBytes)]
        bytesToWrite.extend(dataBytes)
        self.writeEventToFile(bytesToWrite, deltaT=deltaT)

    def writeTempoChange(self, tempo, deltaT = 0):
        self.tempo = tempo
        self.tickLength = 60.0/(tempo * self.quarterNoteDivision)
        microSecondsInQuarter = int(60000000/tempo)

        byteValues = convertNumberToBytes(microSecondsInQuarter, numberOfBytes=3)
        bytesToWrite = [255, 81, 3]
        bytesToWrite.extend(byteValues)

        self.writeEventToFile(bytesToWrite, deltaT=deltaT)

    def writeHeaderChunk(self, midiFormat=0, tracks=1, division=500):
        valuesToWrite = [77, 84, 104, 100]
        valuesToWrite.extend(convertNumberToBytes(6, numberOfBytes=4))
        valuesToWrite.extend(convertNumberToBytes(midiFormat, numberOfBytes=2))
        valuesToWrite.extend(convertNumberToBytes(tracks, numberOfBytes=2))
        valuesToWrite.extend(convertNumberToBytes(division, numberOfBytes=2))

        self.quarterNoteDivision = division
        self.midiFile.write(bytearray(valuesToWrite))

    def writeTrackChunk(self):
        valuesToWrite = [77, 84, 114, 107, 0, 0, 16, 0] #the last 4 values are a placeholder for the actual track length
        self.midiFile.write(bytearray(valuesToWrite))

    def writeTrackLength(self):
        #replace the bytes that five the track length in the track chunk
        #do this after the whole file has been written
        self.midiFile.seek(0, os.SEEK_END)
        byteCount = self.midiFile.tell()

        byteCount = byteCount - 22 #length of track = length of file - 22
        print("track length: %s") %byteCount
        valuesToWrite = convertNumberToBytes(byteCount, numberOfBytes=4)

        self.midiFile.seek(18)
        self.midiFile.write(bytearray(valuesToWrite))

    def convertTicksToMidiDeltaBytes(self, ticks):
        #takes a number of ticks and converts them into an array of ints, according to the MIDI protocol
        deltaTvalues = []
        #calculate values of all bytes
        while(ticks > 127):
            v = ticks % 128
            deltaTvalues.append(v)
            ticks = (ticks - v) / 128
        deltaTvalues.append(ticks)

        midiBytes = []
        thisRange = range(len(deltaTvalues)-1, 0, -1)
        for i in thisRange:
            midiBytes.append(128 + deltaTvalues[i])
        midiBytes.append(deltaTvalues[0])

        return midiBytes



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