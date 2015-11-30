class MidiParser:
    def __init__(self):
        self.fileController = " "

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
        self.midiIterator = ""

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