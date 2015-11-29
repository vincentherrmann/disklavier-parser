import sys
from sys import argv
import array
import os

class DiskEvent:
    def __init__(self, t=0.0, v=0, p=0, eventType = "ks"):
        self.time = t
        self.value = v
        self.eventType = eventType
        self.pitch = p

class DiskNote:
    def __init__(self, p):
        self.pitch = p
        self.keySensor = DiskEvent()
        self.noteOn = DiskEvent()
        self.noteOff = DiskEvent()

class DiskParser:
    def __init__(self):
        self.notes = [] #list of all played DiskNote objects
        self.activeNotes = []
        #self.activeNotes = {int: DiskNote} #dictionary with all currently unfinished notes, max one per pitch
        self.lastEvent = DiskEvent #the latest DiskEvent, for adding additional resolution
        self.events = [] #only for converting from text to midi
        self.midiIterator = ""

    def createEventsFromTextFile(self, file):
        self.events = []
        for line in file:
            #print(line)

            line = line.replace("\t", ", ") #split at tabs
            line = line.replace("; ", ", ") #split at semicolons
            valueList = line.split(", ") #split at commas
            if(len(valueList) != 8):
                continue

            if is_number(valueList[1]) == False:
                continue #this line does not describe a note
            pitch = int(round(float(valueList[1])))
            ksVel = int(round(float(valueList[3]))) #key sensor velocity
            nnVel = int(round(float(valueList[5]))) #note on velocity
            nfVel = int(round(float(valueList[7]))) #note off velocity

            if float(valueList[4]) == 0.0: #if there is no note on time
                if pitch < 127: #if it has a regular pitch (not a pedal event)
                    #ghost note!
                    self.events.append(DiskEvent(p=pitch, t=float(valueList[2]), v=ksVel, eventType="gn")) #ghost event
                    self.events.append(DiskEvent(p=pitch, t=float(valueList[6]), v=0, eventType="gf")) #ghost off event
                    continue

            self.events.append(DiskEvent(p=pitch, t=float(valueList[2]), v=ksVel, eventType="ks")) #key sensor event
            self.events.append(DiskEvent(p=pitch, t=float(valueList[4]), v=nnVel, eventType="nn")) #note on event
            self.events.append(DiskEvent(p=pitch, t=float(valueList[6]), v=nfVel, eventType="nf")) #note off event

        self.events.sort(key = lambda event: event.time)

        # for event in self.events:
        #     print("event at time %s ") %event.time,
        #     print("pitch: %s ") %event.pitch,
        #     print("value %s") %event.value,
        #     print("type: %s ") %event.eventType

    def writeEventsToMidiFile(self):
        lastEventTime = 0
        for event in self.events:
            deltaT = event.time - lastEventTime
            #print("deltaT: %s") %deltaT
            lastEventTime = event.time

            lsValue = int((event.value % 8) * 16) #least significant 3 bits
            msValue = int((event.value - (lsValue/16)) / 8) #most significant 7 bits

            if event.eventType == "ks":
                if event.pitch < 128: #key sensor event
                    self.midiIterator.writeEventToFile(deltaT = deltaT, dataBytes = [160, event.pitch, 28])
                    self.midiIterator.writeEventToFile(dataBytes = [176, 81, msValue])
                    self.midiIterator.writeEventToFile(dataBytes = [176, 16, lsValue])
                elif (p == 191) | (p == 193) | (p == 194): #pedal event
                    ped = p - 127
                    self.midiIterator.writeEventToFile(deltaT = deltaT, dataBytes = [176, ped, msValue])
                    self.midiIterator.writeEventToFile(dataBytes = [176, 16, lsValue])
            if event.eventType == "nn": #note on event
                self.midiIterator.writeEventToFile(deltaT = deltaT, dataBytes = [144, event.pitch, msValue])
                self.midiIterator.writeEventToFile(dataBytes = [176, 16, lsValue])
            if event.eventType == "nf": #note off event
                self.midiIterator.writeEventToFile(deltaT = deltaT, dataBytes = [128, event.pitch, msValue])
                self.midiIterator.writeEventToFile(dataBytes = [176, 16, lsValue])
            if event.eventType == "gn": #ghost note on event
                self.midiIterator.writeEventToFile(deltaT = deltaT, dataBytes = [160, event.pitch, 28])
                self.midiIterator.writeEventToFile(dataBytes = [176, 81, msValue])
                self.midiIterator.writeEventToFile(dataBytes = [176, 16, lsValue])
                self.midiIterator.writeEventToFile(dataBytes = [170, event.pitch, 127])
            if event.eventType == "gf": #ghost note off event
                self.midiIterator.writeEventToFile(deltaT = deltaT, dataBytes = [160, event.pitch, 0])

    def writeSystemEventsToMidiFile(self):
        self.midiIterator.writeEventToFile(dataBytes = [255, 127, 6, 57, 113, 0, 0, 0, 69])
        self.midiIterator.writeEventToFile(dataBytes = [255, 127, 39, 67, 113, 0, 1, 0, 1, 0, 0, 135, 36, 112, 16, 242, 146, 7, 69, 49, 125, 119, 39, 164, 206, 0, 0, 0, 0, 0, 15, 0, 0, 0, 226, 224, 120, 119, 104, 16, 246, 7])
        self.midiIterator.writeEventToFile(dataBytes = [255, 127, 5, 67, 123, 12, 2, 19])

        self.midiIterator.writeEventToFile(dataBytes = [240, 5, 126, 127, 9, 1, 247]) #same
        self.midiIterator.writeEventToFile(dataBytes = [240, 21, 67, 113, 126, 21, 1, 4, 13, 1, 4, 4, 8, 4, 14, 13, 15, 9, 5, 5, 1, 4, 247]) #same
        self.midiIterator.writeEventToFile(deltaT = 4, dataBytes = [240, 8, 67, 16, 76, 0, 0, 126, 0, 247]) #same
        self.midiIterator.writeEventToFile(deltaT = 4, dataBytes = [240, 6, 67, 113, 126, 10, 1, 247]) #same
        self.midiIterator.writeEventToFile(deltaT = 5, dataBytes = [240, 7, 67, 113, 126, 11, 0, 1, 247]) #same
        self.midiIterator.writeEventToFile(deltaT = 0, dataBytes = [240, 7, 67, 113, 126, 11, 1, 1, 247]) #same
        self.midiIterator.writeEventToFile(deltaT = 6, dataBytes = [240, 8, 67, 16, 76, 8, 9, 7, 1, 247]) #same

        self.midiIterator.writeEventToFile(deltaT = 3, dataBytes = [176, 0, 0]) #same
        self.midiIterator.writeEventToFile(deltaT = 4, dataBytes = [176, 32, 0]) #same
        self.midiIterator.writeEventToFile(deltaT = 4, dataBytes = [192, 0]) #same
        self.midiIterator.writeEventToFile(deltaT = 4, dataBytes = [176, 7, 100]) #same

    def processEvent(self, status, p, v, time):
        if status == 176: #additional data resolution
            if p == 81: # first 7 bits of resolution
                self.lastEvent.value = v * 8
            if p == 16: # 3 bits of additional resolution
                self.lastEvent.value += v / 16
            if (p == 64) | (p == 66) | (p == 67): #pedal events
                newEvent = DiskEvent(t = time)
                newEvent.value = v * 8
                self.lastEvent = newEvent
                thisNote = DiskNote(p = 127+p)
                thisNote.keySensor = newEvent
                self.notes.append(thisNote)
            return

        #create new DiskEvent
        newEvent = DiskEvent(t=time, p=p)
        self.lastEvent = newEvent

        if status == 160: #key sensor
            if v == 28: #key sensor of a new note
                #new note
                thisNote = DiskNote(p=p)
                self.activeNotes.append(thisNote)
                #create key sensor event event
                newEvent.eventType = "ks"
                thisNote.keySensor = newEvent
                return

        #look for active notes with same pitch
        notesWithSamePitch = [n for n in self.activeNotes if n.pitch == p]
        if len(notesWithSamePitch) > 0:
            #print("found %s active notes with pitch") %len(notesWithSamePitch),
            #print(p)
            thisNote = notesWithSamePitch[0]
        else:
            thisNote = DiskNote(p=p)
            self.activeNotes.append(thisNote)

        if status == 160:
            if v == 127: #there was a ghost note
                print("ghost note at time %s") %time
            if v == 0: #ghost note released
                newEvent.eventType = "nf"
                thisNote.noteOff = newEvent
                self.finishNote(thisNote)
                print("ghost note released")
        if status == 144: #note on event
            newEvent.eventType = "nn"
            newEvent.value = v * 8
            thisNote.noteOn = newEvent
        if status == 128: #note off event
            #if v == 0:
            #    print("note off velocity 0 at time %s") %time

            newEvent.eventType = "nf"
            newEvent.value = v * 8
            thisNote.noteOff = newEvent

            #submit this note to the notes list
            self.finishNote(thisNote)


    def finishNote(self, thisNote):
        #append thisNote to the note list and delete it from the activeNotes list
        if thisNote.keySensor.time > 0: #don't commit notes with key sensor time 0
            self.notes.append(thisNote)
        else:
            print("deleted note with pitch %s because of missing key sensor value") %thisNote.pitch
        self.activeNotes.remove(thisNote)

    def flushRemainingNotes(self):
        #finish all notes from the activeNotes dict
        for note in self.activeNotes:
            if type(note) == DiskNote:
                self.finishNote(note)

        #sort notes by key sensor time
        self.notes.sort(key = lambda note: note.keySensor.time)

        # print("")
        # for note in self.notes:
        #     print("time: %s") %note.noteOn.time
        #     print("pitch: %s") %note.pitch
        #     print("key sensor: %s") %note.keySensor.value
        #     print("")

    def writeToFile(self, file):
        #header
        text = "Data from Yamaha Disklavier enhanced MIDI format \n"
        text += "note name, pitch, key sensor time, key sensor velocity, note on time, note on velocity, note off time, note off velocity \n"

        #write notes
        for thisNote in self.notes:
            text += "%s, " %self.pitchToNoteName(thisNote.pitch)
            text += "%s, " %thisNote.pitch
            text += "%s, " %thisNote.keySensor.time
            text += "%s, " %thisNote.keySensor.value
            text += "%s, " %thisNote.noteOn.time
            text += "%s, " %thisNote.noteOn.value
            text += "%s, " %thisNote.noteOff.time
            text += "%s \n" %thisNote.noteOff.value

        file.write(text)

    def pitchToNoteName(self, pitch):
        if(pitch < 127):
            c0 = 12
            note = pitch % 12
            octave = (pitch - c0 - note) / 12
            noteName = " "
            if note == 0:
                noteName = "C"
            if note == 1:
                noteName = "C#"
            if note == 2:
                noteName = "D"
            if note == 3:
                noteName = "D#"
            if note == 4:
                noteName = "E"
            if note == 5:
                noteName = "F"
            if note == 6:
                noteName = "F#"
            if note == 7:
                noteName = "G"
            if note == 8:
                noteName = "G#"
            if note == 9:
                noteName = "A"
            if note == 10:
                noteName = "A#"
            if note == 11:
                noteName = "B"

            noteName += "%s" %octave
        elif pitch == 191: #sostenuto pedal
            noteName = "P1"
        elif pitch == 194: #una chorda pedal
            noteName = "P2"
        elif pitch == 193: #middle pedal
            noteName = "P3"

        return noteName



class MidiIterator:
    def __init__(self, parser):
        self.mBytes = [] #the bytes of the midi file
        self.midiFile = ""
        self.byteCount = len(self.mBytes)
        self.i = 0 #current index in the byte list
        self.tickLength = 0.0 #current tick length
        self.currentTime = 0
        self.parser = parser #midi parser

        self.midiFormat = 0
        self.numberOfTracks = 0
        self.quarterNoteDivision = 1
        self.trackLength = 0
        self.tempo = 60

    def readHeaderChunk(self):
        #first 4 bytes are just "MThd" in ASCII
        self.i += 4
        #the next 4 bytes give the number of following data bytes, always 6
        self.i += 4

        #data bytes:
        #the next 16 bits give the midi format
        self.midiFormat = self.mBytes[self.i] * 256 + self.mBytes[self.i+1] #should by 0
        self.i += 2
        #the next 16 bits give the number of tracks
        self.numberOfTracks = self.mBytes[self.i] * 256 + self.mBytes[self.i+1] #should by 0
        self.i += 2
        #the next 16 bits give the division
        if(self.mBytes[self.i] < 128):
            self.quarterNoteDivision = self.mBytes[self.i] * 256 + self.mBytes[self.i+1]
            print("%s divisions per quarter note") %self.quarterNoteDivision
        self.i += 2

    def readTrackChunks(self):
        if(self.midiFormat > 0):
            print("this midi format is not yet implemented")
            return

        #first 4 bytes are just "MTrk" in ASCII
        self.i += 4
        #the next 4 bytes give the number of following data bytes
        for b in range(4): #read 32 bit number
            self.trackLength = self.trackLength * 256 + self.mBytes[self.i]
            self.i += 1
        print("read track with %s bytes") %self.trackLength

        self.readEventStream()

    def readMetaEvent(self):
        if(self.mBytes[self.i] == 255):
            self.i += 1
        else:
            return

        status = self.mBytes[self.i]
        #print("Meta event with status %s") %status
        if status == 81: #tempo change
            self.i += 1
            if self.mBytes[self.i] == 3: #additional identifier byte
                self.i += 1
                #the next 3 bytes give the number of microseconds in one quarter
                microSecondsInQuarter = 0
                for b in range(3): #read 24 bit number
                    microSecondsInQuarter = microSecondsInQuarter * 256 + self.mBytes[self.i]
                    self.i += 1
                self.tempo = 60000000/microSecondsInQuarter
                self.tickLength = 60.0/(self.tempo * self.quarterNoteDivision)
                print("tempo: %s M.M.") %self.tempo
                print("tickLength: %s s") %self.tickLength
                return
        if status == 127: #sequencer specific event with variable length
            self.i += 1 #the byte with this index defines the length of the event
            self.i += self.mBytes[self.i] #skip these bytes
            self.i += 1
            return

    def readSysexEvent(self):
        if(self.mBytes[self.i == 240]):
            self.i += 1
        else:
            return

        #the byte with this index defines the length of the event
        #print("sysex event with %s bytes") %self.mBytes[self.i]
        self.i += self.mBytes[self.i] #skip these bytes
        self.i += 1


    def readEventStream(self):
        while self.i < (self.byteCount - 2):
            #print("read byte number %s") %self.i

            #timecode: n bytes with MSB=1, followed by one byte with MSB=0
            deltaT = 0
            while (self.mBytes[self.i] > 127): #for all bytes with MSB=1
                deltaT = deltaT * 128 + (self.mBytes[self.i] - 128)
                self.i += 1
            deltaT = deltaT * 128 + self.mBytes[self.i]

            if deltaT > 0: #print deltaT
                self.currentTime += (deltaT * self.tickLength)
                #print(" time: %s") %self.currentTime
            self.i += 1

            #event: one byte with MSB=1, followed by n bytes with MSB=0
            status = self.mBytes[self.i]
            #print("status: %s") %status
            if status < 128:
                continue
            if status == 255:
                self.readMetaEvent()
                continue
            if status == 240:
                self.readSysexEvent()
                continue
            if (status >= 192) & (status <224):
                #short event with one data byte
                #print("short event with status %s") %status
                parser.processEvent(status, p = self.mBytes[self.i+1], v=0, time=self.currentTime)
                self.i += 2
                continue
            if self.mBytes[self.i+2] < 128:
                parser.processEvent(status, p = self.mBytes[self.i+1], v=self.mBytes[self.i+2], time=self.currentTime)
                self.i += 3

        self.parser.flushRemainingNotes()

    def writeEventToFile(self, deltaT = 0, dataBytes = [0]):
        if (deltaT > 0) & (self.tickLength > 0):
            ticks = int((deltaT / self.tickLength) + 0.5) #+0.5 to round correctly
        else:
            ticks = 0
        #print("deltaTicks: %s ") %ticks,
        #print("tick length: %s ") %self.tickLength
        self.midiFile.write(bytearray(self.convertTicksToMidiDeltaBytes(ticks=ticks)))
        #print("write event %s to file") %dataBytes
        self.midiFile.write(bytearray(dataBytes))

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

    def writeTempoChange(self, tempo, deltaT = 0):
        self.tempo = tempo
        self.tickLength = 60.0/(tempo * self.quarterNoteDivision)
        print("tickLenght: %s") %self.tickLength
        microSecondsInQuarter = int(60000000/tempo)

        byteValues = self.convertNumberToBytes(microSecondsInQuarter, numberOfBytes=3)
        valuesToWrite = [255, 81, 3]
        valuesToWrite.extend(byteValues)
        #print("tempo change values %s") %valuesToWrite
        self.writeEventToFile(deltaT=deltaT, dataBytes=valuesToWrite)

    def writeHeaderChunk(self, midiFormat=0, tracks=1, division=500):
        valuesToWrite = [77, 84, 104, 100]
        valuesToWrite.extend(self.convertNumberToBytes(6, numberOfBytes=4))
        valuesToWrite.extend(self.convertNumberToBytes(midiFormat, numberOfBytes=2))
        valuesToWrite.extend(self.convertNumberToBytes(tracks, numberOfBytes=2))
        valuesToWrite.extend(self.convertNumberToBytes(division, numberOfBytes=2))

        self.quarterNoteDivision = division
        self.midiFile.write(bytearray(valuesToWrite))

    def writeTrackChunk(self):
        valuesToWrite = [77, 84, 114, 107, 0, 0, 16, 0]
        self.midiFile.write(bytearray(valuesToWrite))

    def writeTrackLength(self):
        #replace the bytes that five the track length in the track chunk
        #do this after the whole file has been written
        self.midiFile.seek(0, os.SEEK_END)
        byteCount = self.midiFile.tell()

        byteCount = byteCount - 22 #length of track = length of file - 22
        print("track length: %s") %byteCount
        valuesToWrite = self.convertNumberToBytes(byteCount, numberOfBytes=4)

        self.midiFile.seek(18)
        self.midiFile.write(bytearray(valuesToWrite))

    def convertNumberToBytes(self, number, numberOfBytes=1):
        byteValues = []

        #print("number to convert to bytes: %s") %number
        for i in range(numberOfBytes):
            thisByte = number % 256
            byteValues.append(thisByte)
            number = (number - thisByte) / 256

        byteValues.reverse()
        #print("number as bytes: %s") %byteValues
        return byteValues

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

###################################################################################
if len(argv) == 2:
    script, filename = argv
    should_print_values = " "
elif len(argv) == 3:
    script, filename, should_print_values = argv

#choose apropriate behaviour
fileEnding = filename[-4:]
if (fileEnding == ".mid") | (fileEnding == ".MID"):
    print("converting MIDI file to text")
    #read all bytes of midi file
    bytes_read = open(filename, "rb").read()

    #parse the file
    parser = DiskParser()
    iterator = MidiIterator(parser=parser)
    iterator.mBytes = map(ord, bytes_read)
    iterator.byteCount = len(iterator.mBytes)
    iterator.readHeaderChunk()
    iterator.readTrackChunks()

    #create text file
    filename_conv = filename[:-4]
    filename_conv = filename_conv + "_data.txt"
    print("converted filename: %s") %filename_conv
    file_conv = open(filename_conv, "w")

    #let parser write to this file
    parser.writeToFile(file_conv)
elif fileEnding == ".txt":
    #read events from text file
    print("converting text file to MIDI")
    parser = DiskParser()


    #create midi file
    filename_conv = filename[:-4]
    filename_conv = filename_conv + ".mid"
    print("converted filename: %s") %filename_conv
    file_conv = open(filename_conv, "wb")

    #create MIDI iterator to write the MIDI file
    iterator = MidiIterator(parser = parser)
    iterator.midiFile = file_conv
    parser.midiIterator = iterator

    #write the MIDI file
    iterator.writeHeaderChunk(division = 600)
    iterator.writeTrackChunk()
    iterator.writeTempoChange(tempo=400)

    parser.createEventsFromTextFile(open(filename, "r"))
    parser.writeSystemEventsToMidiFile()
    parser.writeEventsToMidiFile()

    file_conv.close()
    file_conv = open(filename_conv, "r+b")
    iterator.midiFile = file_conv
    iterator.writeTrackLength()

    file_conv.close()

    ##print newly written bytes
    # bytes_read = open(filename_conv, "rb").read()
    # print("read %s bytes from new file:") %len(bytes_read)
    # for j in range(len(bytes_read)):
    #     b = ord(bytes_read[j])
    #     if(b > 127):
    #         print(" ")
    #     print(b),
else:
    print("can't handle a file of type %s") %fileEnding
    sys.exit("unknown file type")


# print bytes
# j = 0
# for j in range(len(bytes_read)):
#    b = ord(bytes_read[j])
#    if (b > 127):
#        print(" ")
#    print(b),
#
# print("")

