import midi
import urllib
import urllib2
import json
import math
import datetime
import sys
import os.path

resolution = 256

from config import *

wikiApiUrl = 'https://www.wikidata.org/w/api.php'

if len(sys.argv) != 3:
    print "Usage: {0} <qid> <output-dir>".format( sys.argv[0] )
    sys.exit(2)

def makeTrack( midiFile, rc ):
	# Instantiate a MIDI Pattern (contains a list of tracks)
	pattern = midi.Pattern( resolution = resolution )
	# Instantiate a MIDI Track (contains a list of MIDI events)
	track = midi.Track()
	# Append the track to the pattern
	pattern.append(track)

	# Instantiate a MIDI note on event, append it to the track
	for row in rc:
		pitch = midi.C_3 + ( row['userid'] % 12 );
		
		args = { 
			'tick': get_pause( row ),
			'pitch': get_pitch( row ),
			'velocity': get_velocity( row ),
		}
		
		track.append( midi.NoteOnEvent( **args ) )
		
		args['tick'] = get_sustain( row )
		track.append( midi.NoteOffEvent( **args ) )
	
	# Add the end of track event, append it to the track
	eot = midi.EndOfTrackEvent(tick=1)
	track.append(eot)
	
	# Save the pattern to disk
	midi.write_midifile( midiFile, pattern )
	
def readCsv( filename ):
	rows = []
	fields = None
	
	f = open( filename, 'rb')
	
	for line in f:
		row = line.decode('utf8').split( "\t" )

		if fields is None:
			fields = row
			continue
			
		values = dict( zip( fields, row ) )
		
		values['size'] = int( values['size'] )
		values['delta-size'] = int( values['delta-size'] )
		values['delta-time'] = int( values['delta-time'] )
		values['userid'] = int( values['userid'] )
		
		rows.append( values )
		
	f.close()
	return rows
	
csvfile = sys.argv[1]
midifile = sys.argv[2]

if not os.path.exists( csvfile ):
	print "Cannot find ", csvfile
	quit(3)

if os.path.isdir( midifile ):
	( name, ext ) = os.path.splitext( os.path.basename( csvfile ) )
	midifile = "%s/%s.mid" % ( midifile, name )
	
print "Loading events from", csvfile
rc = readCsv( csvfile )
makeTrack( midifile, rc )
print "MIDI written to ", midifile