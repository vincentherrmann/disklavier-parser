from midiFileController import MidiFileController
from disklavierParser import MidiParser, DisklavierParser
from sys import argv
import sys

script, filename = argv

parser = DisklavierParser()
controller = MidiFileController(parser=parser)
parser.midiController = controller

fileEnding = filename[-4:]
if (fileEnding == ".mid") | (fileEnding == ".MID"):
    print("opening MIDI file")
    midiBytes = open(filename, "rb").read()

    #read bytes from MIDI file
    controller.mBytes = map(ord, midiBytes)
    controller.readHeaderChunk()
    controller.readTrackChunks()

    #create text file
    filename_conv = filename[:-4]
    filename_conv = filename_conv + "_data.txt"
    print("converted filename: %s") %filename_conv
    file_conv = open(filename_conv, "w")

    #write text file
    parser.writeToTextFile(file_conv)

    file_conv.close()
elif fileEnding == ".txt":
    print("opening text file")
    textFile = open(filename, "r")

    #read midi events from text file
    parser.createEventsFromTextFile(textFile)

    #create MIDI file
    filename_conv = filename[:-4]
    filename_conv = filename_conv + ".mid"
    print("converted filename: %s") %filename_conv
    file_conv = open(filename_conv, "wb")
    controller.midiFile = file_conv

    #write MIDI file
    controller.writeHeaderChunk(division=600)
    controller.writeTrackChunk()
    controller.writeTempoChange(tempo=400)
    parser.writeSetupEvents()
    parser.writeEventsToMidiFile()

    #write track length
    file_conv.close()
    file_conv = open(filename_conv, "r+b")
    controller.midiFile = file_conv
    controller.writeTrackLength()

    file_conv.close()
else:
    print("can't handle a file of type %s") %fileEnding
    sys.exit("unknown file type")
