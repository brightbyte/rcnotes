from midi import *
import sys

if len(sys.argv) != 2:
    print "Usage: {0} <midifile>".format(sys.argv[0])
    sys.exit(2)
    
class TrackBuilder:
	bottom = 0
	tick = 0
	pending = []

	def __init__( self, duration = 60, velocity = 70, channel = 0 ):
		self.duration = duration
		self.velocity = velocity
		self.channel = channel
		
		self.track = Track( tick_relative = False )
		
	def _defaults( self, kw ):
		if not 'tick' in kw:
			kw['tick'] = self.tick
			
		if not 'channel' in kw:
			kw['channel'] = self.channel
		
	def note( self, pitch, **kw ):
		kw['pitch'] = pitch
		if not 'duration' in kw:
			kw['duration'] = self.duration

		if not 'velocity' in kw:
			kw['velocity'] = self.velocity
			
		self._defaults(kw)
		
		self.flush( kw['tick'] )
		self._commit( NoteOnEvent( **kw ) )
		
		kw['tick'] = kw['tick'] + kw['duration']
		self._queue( NoteOffEvent( **kw ) )
		
		return self.tick
	
	def control( self, value, **kw ):
		kw['value'] = value
		self._defaults(kw)

		self.flush( kw['tick'] )
		self._commit( ControlChangeEvent( **kw ) )
	
	def program( self, value, **kw ):
		kw['value'] = value
		self._defaults(kw)

		self.flush( kw['tick'] )
		self._commit( ProgramChangeEvent( **kw ) )
		
	def _commit( self, event ):
		if ( event.tick < self.bottom ):
			raise Exception( "Cannot commit past events! %i < %i" % ( event.tick, self.bottom ) )
		
		self.track.append( event )
		self.bottom = event.tick
		self.tick = max( self.tick, self.bottom )

	def _queue( self, event ):
		if ( event.tick < self.bottom ):
			raise Exception( "Cannot queue past events! %i < %i" % ( event.tick, self.bottom ) )
		
		self.pending.append( event )
		self.tick = max( self.tick, event.tick )
		
	def flush( self, upto = None ):
		queue = sorted( self.pending, key = lambda event: event.tick )
		self.pending = []
		
		for event in queue:
			if upto is None or event.tick < upto:
				self._commit( event )
			else:
				self._queue( event )
	
	def seek( self, tick ):
		if ( tick < self.bottom ):
			raise Exception( "Cannot seek back past played notes! %i < %i" % ( event.tick, self.bottom ) )
		
		self.tick = tick
	
	def shift( self, ticks ):
		self.seek( self.tick + ticks )
	
	def pause( self, notes ):
		self.shift( notes * self.duration )
		
	def close( self ):
		self.flush()
		self.track.append( EndOfTrackEvent( tick = self.tick ) )
		
		track = self.track
		self.track = None
		return track

class ChordBuilder:
	def __init__( self, trackBuilder ):
		self.tick = trackBuilder.tick
		self.trackBuilder = trackBuilder
		
	def note( self, pitch, **kw ):
		kw['pitch'] = pitch
		
		if not 'tick' in kw:
			kw['tick'] = self.tick
		
		self.trackBuilder.note( **kw )
    
def makeTrack():
	builder = TrackBuilder()
	
	builder.note( C_3 )
	builder.note( E_3 )
	builder.note( G_3 )
	builder.note( C_4 )
	builder.pause( 2 )
	
	chord = ChordBuilder( builder )
	chord.note( C_3 )
	chord.note( E_3 )
	chord.note( G_3 )
	chord.note( C_4 )

	return builder.close()
	
def makeMidiFile( midifile ):
	# Instantiate a MIDI Pattern (contains a list of tracks)
	pattern = Pattern( format = 1, resolution= 220, tick_relative=False )

	track = makeTrack()
	pattern.append(track)

	print pattern
	
	# Save the pattern to disk
	write_midifile(midifile, pattern)

    
midifile = sys.argv[1]
makeMidiFile( midifile )
