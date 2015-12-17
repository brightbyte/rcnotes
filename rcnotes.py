import midi
import urllib
import urllib2
import json
import math
import datetime
import sys

wikiApiUrl = 'https://www.wikidata.org/w/api.php'

if len(sys.argv) != 2:
    print "Usage: {0} <midifile>".format( sys.argv[0] )
    sys.exit(2)
    
def fetchRecentChanges( title, **params ):
	url = wikiApiUrl
	
	params['titles'] = title
	
	if not 'rvlimit' in params:
		params['rvlimit'] = 100

	if not 'rvprop' in params:
		params['rvprop'] = 'ids|timestamp|userid|flags|tages|size|comment'

	params['action'] = 'query'
	params['prop'] = 'revisions'
	params['rvdir'] = 'newer'
	params['format'] = 'json'
	
	url = url + '?' + urllib.urlencode( params )
	
	print url
	response = urllib2.urlopen( url )
	if response.getcode() >= 400:
		raise Exception( 'HTTP error: ' + response.getcode() + "\nFrom: " + response.geturl() )
	
	if response.info().getsubtype() != 'json':
		raise Exception( 'Not JSON: ' + response.info().gettype() + "\nFrom: " + response.geturl() )
	
	jsonString = response.read()
	apiResponse = json.loads( jsonString )
	
	for id, pageData in apiResponse['query']['pages'].items():
		break #all we need is the first value in pageData
	
	return pageData['revisions']

def isoTimeDelta( aTime, bTime ):
	a = datetime.datetime.strptime( aTime, "%Y-%m-%dT%H:%M:%SZ" )
	b = datetime.datetime.strptime( bTime, "%Y-%m-%dT%H:%M:%SZ" )
	
	delta = a - b
	return int( delta.total_seconds() )

def addDeltas( revisions ):
	revisionsWithDeltas = []
	prev = None
	for rev in revisions:
		newRow = rev
		
		if prev is None:
			newRow['delta-timestamp'] = 0
			newRow['delta-timestamp-log'] = 0
			newRow['delta-size'] = rev['size']
			newRow['delta-size-log'] = int( round( math.log( newRow['delta-size'] ) ) )
		else:
			newRow['delta-timestamp'] = isoTimeDelta( rev['timestamp'], prev['timestamp'] )
			newRow['delta-timestamp-log'] = int( round( math.log( newRow['delta-timestamp'] ) ) )
			newRow['delta-size'] = rev['size'] - prev['size']
			newRow['delta-size-log'] = int( round( math.log( newRow['delta-size'] ) ) )
			
		prev = rev
		revisionsWithDeltas.append( newRow )
		
	return revisionsWithDeltas

def makeTrack( midiFile, rc ):
	# Instantiate a MIDI Pattern (contains a list of tracks)
	pattern = midi.Pattern()
	# Instantiate a MIDI Track (contains a list of MIDI events)
	track = midi.Track()
	# Append the track to the pattern
	pattern.append(track)

	# Instantiate a MIDI note on event, append it to the track
	for row in rc:
		args = { 
			'tick': row['delta-timestamp-log'] * 10,
			'pitch': midi.G_3,
			'velocity': min( 255, row['delta-size-log'] * 16 )
		}
		
		print args
		track.append( midi.NoteOnEvent( **args ) )
	
	# Add the end of track event, append it to the track
	eot = midi.EndOfTrackEvent(tick=1)
	track.append(eot)
	
	# Print out the pattern
	print pattern
	# Save the pattern to disk
	midi.write_midifile( midiFile, pattern )
	
rc = fetchRecentChanges( 'Q154556', rvstart = '2015-01-01T00:00:00Z' )
rc = addDeltas( rc )
# for row in rc:
# 	print row['revid'], row['timestamp'], '//', row['delta-size'], row['delta-timestamp'], '//', row['delta-size-log'], row['delta-timestamp-log']

midifile = sys.argv[1]
makeTrack( midifile, rc )