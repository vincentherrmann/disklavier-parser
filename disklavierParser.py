

class MidiParser:
    def __init__(self):
        self.midiController = ""

    #process event with status byte and two data bytes p and v at given time
    def processStandardEvent(self, status, p, v, time):
        print("event at time %s") %time
        print([status, p, v])

    #process system exlusive event with a flexible number of data bytes at given time
    def processSysexEvent(self, bytes, time):
        print("system exclusive event at time %s") %time
        print(bytes)

    #process sequencer specific event with a flexible number of data bytes at given time
    def processSequencerEvent(self, bytes, time):
        print("sequencer specific event at time %s") %time
        print(bytes)

    #write currently available information to a text file
    def writeToTextFile(self, file):
        text = "Data from MIDI file"
        file.write(text)

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

class DisklavierParser(MidiParser):
    def __init__(self):
        self.notes = [] #list of all player DiskNote objects
        self.activeNotes = []
        self.lastEvent = DiskEvent #the latest DiskEvent, for adding additional resolution
        self.events = [] #only for converting from text to midi
        self.midiController = " "

    def processStandardEvent(self, status, p, v, time):
        #additional data resolution or pedal event
        if status == 176:
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

        #key sensor event
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
        if len(notesWithSamePitch) > 0: #if are active notes with same pitch, set thisNote to the first
            thisNote = notesWithSamePitch[0]
        else: #if not, create new note with pitch p and add it to the active notes
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
            newEvent.eventType = "nf"
            newEvent.value = v * 8
            thisNote.noteOff = newEvent

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

    def writeToTextFile(self, file):
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

    def createEventsFromTextFile(self, file):
        self.events = []
        for line in file:
            line = line.replace("\t", ", ") #split at tabs
            line = line.replace("; ", ", ") #split at semicolons
            valueList = line.split(", ") #split at commas

            #make sure this line represents a note
            if(len(valueList) != 8):
                continue
            if is_number(valueList[1]) == False:
                continue

            #get values
            pitch = int(round(float(valueList[1])))
            ksTime = float(valueList[2])
            ksVel = int(round(float(valueList[3]))) #key sensor velocity
            nnTime = float(valueList[4])
            nnVel = int(round(float(valueList[5]))) #note on velocity
            nfTime = float(valueList[6])
            nfVel = int(round(float(valueList[7]))) #note off velocity

            #split notes in individual events
            if nnTime == 0.0: #if there is no note on time
                if pitch < 127: #if it has a regular pitch (not a pedal event)
                    #ghost note!
                    self.events.append(DiskEvent(p=pitch, t=ksTime, v=ksVel, eventType="gn")) #ghost event
                    self.events.append(DiskEvent(p=pitch, t=nfTime, v=0, eventType="gf")) #ghost off event
                    continue
            self.events.append(DiskEvent(p=pitch, t=ksTime, v=ksVel, eventType="ks")) #key sensor event
            self.events.append(DiskEvent(p=pitch, t=nnTime, v=nnVel, eventType="nn")) #note on event
            self.events.append(DiskEvent(p=pitch, t=nfTime, v=nfVel, eventType="nf")) #note off event

        #sort events by time
        self.events.sort(key = lambda event: event.time)

    def writeEventsToMidiFile(self):
        lastEventTime = 0
        for event in self.events:
            deltaT = event.time - lastEventTime
            lastEventTime = event.time

            p = event.pitch
            lsValue = int((event.value % 8) * 16) #least significant 3 bits
            msValue = int((event.value - (lsValue/16)) / 8) #most significant 7 bits

            if event.eventType == "ks":
                if p < 128: #key sensor event
                    self.midiController.writeEventToFile(deltaT = deltaT, dataBytes = [160, p, 28])
                    self.midiController.writeEventToFile(dataBytes = [176, 81, msValue])
                    self.midiController.writeEventToFile(dataBytes = [176, 16, lsValue])
                elif (p == 191) | (p == 193) | (p == 194): #pedal event
                    ped = p - 127
                    self.midiController.writeEventToFile(deltaT = deltaT, dataBytes = [176, ped, msValue])
                    self.midiController.writeEventToFile(dataBytes = [176, 16, lsValue])
            if event.eventType == "nn": #note on event
                self.midiController.writeEventToFile(deltaT = deltaT, dataBytes = [144, p, msValue])
                self.midiController.writeEventToFile(dataBytes = [176, 16, lsValue])
            if event.eventType == "nf": #note off event
                self.midiController.writeEventToFile(deltaT = deltaT, dataBytes = [128, p, msValue])
                self.midiController.writeEventToFile(dataBytes = [176, 16, lsValue])
            if event.eventType == "gn": #ghost note on event
                self.midiController.writeEventToFile(deltaT = deltaT, dataBytes = [160, p, 28])
                self.midiController.writeEventToFile(dataBytes = [176, 81, msValue])
                self.midiController.writeEventToFile(dataBytes = [176, 16, lsValue])
                self.midiController.writeEventToFile(dataBytes = [170, p, 127])
            if event.eventType == "gf": #ghost note off event
                self.midiController.writeEventToFile(deltaT = deltaT, dataBytes = [160, p, 0])

    def writeSetupEvents(self):
        self.midiController.writeSequencerEvent([57, 113, 0, 0, 0, 69])
        self.midiController.writeSequencerEvent([67, 113, 0, 1, 0, 1, 0, 0, 135, 36, 112, 16, 242, 146, 7, 69, 49, 125, 119, 39, 164, 206, 0, 0, 0, 0, 0, 15, 0, 0, 0, 226, 224, 120, 119, 104, 16, 246, 7])
        self.midiController.writeSequencerEvent([67, 123, 12, 2, 19])

        self.midiController.writeSysexEvent(deltaT=0, dataBytes=[126, 127, 9, 1, 247])
        self.midiController.writeSysexEvent(deltaT=0, dataBytes=[67, 113, 126, 21, 1, 4, 13, 1, 4, 4, 8, 4, 14, 13, 15, 9, 5, 5, 1, 4, 247])
        self.midiController.writeSysexEvent(deltaT=4, dataBytes=[67, 16, 76, 0, 0, 126, 0, 247])
        self.midiController.writeSysexEvent(deltaT=4, dataBytes=[67, 113, 126, 10, 1, 247])
        self.midiController.writeSysexEvent(deltaT=5, dataBytes=[67, 113, 126, 11, 0, 1, 247])
        self.midiController.writeSysexEvent(deltaT=0, dataBytes=[67, 113, 126, 11, 1, 1, 247])
        self.midiController.writeSysexEvent(deltaT=6, dataBytes=[67, 16, 76, 8, 9, 7, 1, 247])

        self.midiController.writeEventToFile(deltaT=3, dataBytes=[176, 0, 0])
        self.midiController.writeEventToFile(deltaT=3, dataBytes=[176, 32, 0])
        self.midiController.writeEventToFile(deltaT=3, dataBytes=[192, 0])
        self.midiController.writeEventToFile(deltaT=3, dataBytes=[176, 7, 100])



def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False