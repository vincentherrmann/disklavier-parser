from midiFileController import MidiFileController
from disklavierParser import MidiParser, DisklavierParser
from sys import argv

script, filename = argv

parser = DisklavierParser()
controller = MidiFileController(parser=parser)

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

    parser.writeToTextFile(file_conv)