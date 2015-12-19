# Configuration for rc2mini.
# This is a regular python module.
# Definitions here can be changed to modify the behavior of rc2midi

# import modules for use in mapping functions
from midi import *
import math

# utility function for log
def logish( n ):
	n = -n if n < 0 else n
	
	if n < 1: 
		return 0
	else:
		return int( round( math.log( n ) ) )

# midi setup
resolution = 256

# E flat minor scale, used by get_pitch()
pitches = [ Eb_3, F_3, Gb_3, Ab_3, Bb_3, Cs_3, Db_3 ]

# Mapping functions
# the following numeric fields are defined in the edit parameter:
#   userid, size, delta-size, delta-time
# the following additional fields are available:
#   timestamp, user, comment

# function producting the pitch value
def get_pitch( edit ):
	p = edit['userid'] % len( pitches )
	return pitches[p]

# function producting the pitch value
def get_velocity( edit ):
	return min( 255, logish( edit['delta-size'] ) * 16 )

# Function producting pause (in ticks) after the release of the previous note.
def get_pause( edit ):
	return logish( edit['delta-time'] ) * 16 + 16

# function producting the number of ticks before the note is released.
def get_sustain( edit ):
	# as long as the pause
	return get_pause( edit )

