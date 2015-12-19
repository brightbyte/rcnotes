import midi
import urllib
import urllib2
import json
import math
import datetime
import sys
import os.path

wikiApiUrl = 'https://www.wikidata.org/w/api.php'

if len(sys.argv) != 3:
    print "Usage: {0} <title> <output-dir>".format( sys.argv[0] )
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
	
	print "Fetching data from", url
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
			newRow['delta-time'] = 0
			newRow['delta-size'] = rev['size']
		else:
			newRow['delta-time'] = isoTimeDelta( rev['timestamp'], prev['timestamp'] )
			newRow['delta-size'] = rev['size'] - prev['size']
			
		prev = rev
		revisionsWithDeltas.append( newRow )
		
	return revisionsWithDeltas
	
def writeCsv( filename, rc ):
	f = open( filename, 'wb')
	
	fields = (
		'revid',
		'timestamp', 
		'delta-time',
		'size',
		'delta-size',
		'userid',
		'user',
		'comment',
	)

	s = u"%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % fields
	f.write( s.encode('utf8') )
	
	for row in rc:
		fields = ( row['revid'],
			row['timestamp'], 
			row['delta-time'],
			row['size'],
			row['delta-size'],
			row['userid'],
			row['user'] if 'user' in row else "",
			row['comment'] if 'comment' in row else "",
		)

		s = u"%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % fields
		f.write( s.encode('utf8') )
		
	f.close()
	
title = sys.argv[1]
csvfile = sys.argv[2]

if os.path.isdir( csvfile ):
	csvfile = "%s/%s.csv" % ( csvfile, title )

rc = fetchRecentChanges( title )
rc = addDeltas( rc )

writeCsv( csvfile, rc )
print "Events written to ", csvfile
