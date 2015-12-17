import midi
import urllib
import urllib2
import json
import math
import datetime
import sys

wikiApiUrl = 'https://www.wikidata.org/w/api.php'

if len(sys.argv) != 3:
    print "Usage: {0} <qid> <output-dir>".format( sys.argv[0] )
    sys.exit(2)
    
def fetchRecentChanges( title, **params ):
	url = wikiApiUrl
	
	params['titles'] = title
	
	if not 'rvlimit' in params:
		params['rvlimit'] = 500

	if not 'rvprop' in params:
		params['rvprop'] = 'ids|timestamp|user|userid|flags|tages|size|comment'

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

def logish( n ):
	if n < 1: 
		return 0
	else:
		return int( round( math.log( n ) ) )


def addDeltas( revisions ):
	revisionsWithDeltas = []
	prev = None
	for rev in revisions:
		newRow = rev
		
		if prev is None:
			newRow['delta-timestamp'] = 0
			newRow['delta-timestamp-log'] = 0
			newRow['delta-size'] = rev['size']
			newRow['delta-size-log'] = logish( newRow['delta-size'] )
		else:
			newRow['delta-timestamp'] = isoTimeDelta( rev['timestamp'], prev['timestamp'] )
			newRow['delta-timestamp-log'] = logish( newRow['delta-timestamp'] )
			newRow['delta-size'] = rev['size'] - prev['size']
			newRow['delta-size-log'] = logish( newRow['delta-size'] )
			
		prev = rev
		revisionsWithDeltas.append( newRow )
		
	return revisionsWithDeltas

def makeTrack( midiFile, rc ):
	# Instantiate a MIDI Pattern (contains a list of tracks)
	pattern = midi.Pattern( resolution=256 )
	# Instantiate a MIDI Track (contains a list of MIDI events)
	track = midi.Track()
	# Append the track to the pattern
	pattern.append(track)

	# Instantiate a MIDI note on event, append it to the track
	for row in rc:
		pitch = midi.C_3 + ( row['userid'] % 12 );
		
		args = { 
			'tick': row['delta-timestamp-log'] * 16 + 16,
			'pitch': pitch,
			'velocity': min( 255, abs( row['delta-size-log'] ) * 16 )
		}
		
		print args
		track.append( midi.NoteOnEvent( **args ) )
		track.append( midi.NoteOffEvent( **args ) )
	
	# Add the end of track event, append it to the track
	eot = midi.EndOfTrackEvent(tick=1)
	track.append(eot)
	
	# Save the pattern to disk
	midi.write_midifile( midiFile, pattern )
	
def writeCsv( filename, rc ):
	f = open( filename, 'wb')
	
	fields = (
		'revid',
		'timestamp', 
		'delta-size',
		'delta-size-log',
		'delta-timestamp',
		'delta-timestamp-log',
		'user',
		'userid',
		'comment',
	)

	s = u"%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % fields
	f.write( s.encode('utf8') )
	
	for row in rc:
		fields = ( row['revid'],
			row['timestamp'], 
			row['delta-size'],
			row['delta-size-log'],
			row['delta-timestamp'],
			row['delta-timestamp-log'],
			row['user'],
			row['userid'],
			row['comment'],
		)

		s = u"%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % fields
		f.write( s.encode('utf8') )
		
	f.close()
	
qid = sys.argv[1]
rc = fetchRecentChanges( qid )
rc = addDeltas( rc )

csvfile = sys.argv[2] + "/" + qid + ".csv"
writeCsv( csvfile, rc )
print csvfile

midifile = sys.argv[2] + "/" + qid + ".mid"
makeTrack( midifile, rc )
print midifile
