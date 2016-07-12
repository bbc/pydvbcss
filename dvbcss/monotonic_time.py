#!/usr/bin/env python
#
# Copyright 2015 British Broadcasting Corporation
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#	  http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""\

This module implements operating system specific access to high resolution
monotonic system timers for the following operating systems:

 * Windows 2000 Pro or later
 * Linux
 * Mac OS X
 
It implements a :func:`time` function and :func:`sleep` function that work
the same as the :func:`time.time` and :func:`time.sleep` functions in the
python standard library.

It also adds a :func:`timeNanos` and :func:`timeMicros` variants that report
time in units of nanoseconds or microseconds instead of seconds.

See operating system specific implementation details below to understand
the limitations of the functions provided in this module.

.. note::

   For all supported operating systems, the sleep() function is not guaranteed
   to use the same underlying timer as the time() and therefore should be
   considered inaccurate.

Example use
-----------

.. code-block:: python

	>>> import dvbcss.monotonic_time as monotonic_time
	>>> monotonic_time.time()
	4695.582637038
	>>> monotonic_time.timeNanos()
	4700164952506L
	>>> monotonic_time.timeMicros()
	4703471405L
	>>> monotonic_time.sleep(0.5)	# sleep 1/2 second


Operating system implementation details
---------------------------------------

The precision and accuracy of the clocks and sleep functions are dependent on
the host operating system and hardware. This module can therefore provide no
performance guarantees.

Windows
~~~~~~~

Windows NT 5.0 (Windows 2000 Professional) or later is supported, including
the cygwin environment.

The :func:`time` function and its variants are based on the 
`QueryPerformanceCounter() <http://msdn.microsoft.com/en-us/library/windows/desktop/ms644904.aspx>`_
high resolution timer system call.
This clock is guaranteed to be monotonic and have 1 microsecond precision or better.

The :func:`sleep` function is based on the
`CreateWaitableTimer() and SetWaitableTimer() <http://msdn.microsoft.com/en-us/library/windows/desktop/ms687008.aspx>`_
system calls.

Note that the :func:`sleep` function for Windows is not guaranteed to be accurate
because it is not possible to create blocking (non polling) delays
based on the clock source used. However it should have significantly
higher precision than the standard 15ms windows timers and will be fine
for short delays.

Mac OS X
~~~~~~~~

The :func:`time` function and its variants are based on the
`mach_absolute_time() <https://developer.apple.com/library/mac/qa/qa1398/_index.html>`_
system call. 

The clock is guaranteed to be monotonic. Apple provides no guarantees on precision,
however in practice it is usually based on hardware tick counters in the processor or
support chips and so is extremely high precision (microseconds or better).

The :func:`sleep` function is based on the
`nanosleep() <https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man2/nanosleep.2.html>`_
system call. It is unclear whether this uses the same underlying counter as `mach_absolute_time()`.

Linux
~~~~~

The :func:`time` function and its variants are based on the
`clock_gettime() <http://linux.die.net/man/3/clock_gettime>`_
system call requesting `CLOCK_MONOTONIC`.

The :func:`sleep` function is based on the
`nanosleep() <http://linux.die.net/man/3/nanosleep>`_
system call. It is unclear whether this uses the same underlying counter as `CLOCK_MONOTONIC`.



"""

from exceptions import NotImplementedError
from exceptions import RuntimeError
import os
import sys

__all__ = ["TimeoutError", "InterruptedException", "time", "timeNanos", "timeMicros", "sleep"]

def _expose(func):
	global __all__
	__all__.append(func.__name__)
	return func

@_expose
def time():
	"""\
	Return monotonic time in seconds and fractions of seconds (as a float). The precision is operating system dependent.
	"""
	raise RuntimeError("Module was unable to initialise successfully. Function not available.")

@_expose
def timeNanos():
	"""\
	Return monotonic time in integer nanoseconds. The precision is operating system dependent.
	"""
	raise RuntimeError("Module was unable to initialise successfully. Function not available.")

@_expose
def timeMicros():
	"""\
	Return monotonic time in integer microseconds. The precision is operating system dependent.
	"""
	raise RuntimeError("Module was unable to initialise successfully. Function not available.")

@_expose
def sleep(secs):
	"""\
	Sleep for specified number of second and fractions of seconds (as a float).	 The precision is operating system dependent.
	
	:throws TimeoutError: if the underlying system call used to sleep reported a timeout (OS dependent behaviour)
	:throws InterruptedException: if a signal or other interruption is received while sleeping (OS dependent behaviour)

	.. note::
	
	   For all supported operating systems, the sleep() function is not guaranteed
	   to use the same underlying timer as the time() and therefore should be
	   considered inaccurate.

	"""
	raise RuntimeError("Module was unable to initialise successfully. Function not available.")

# ==========================================================================

class TimeoutError(Exception):
		def __init__(self,*args,**kwargs):
			super(TimeoutError,self).__init__(*args,**kwargs)

class InterruptedException(Exception):
		def __init__(self,*args,**kwargs):
			super(InterruptedException,self).__init__(*args,**kwargs)


# ==========================================================================

def _Darwin_init():
	"""\
	Sets functions that retrieves time based on system monotonic timer.
	
	For mac os x (Darwin kernel) this is based on mach_absolute_time()
	"""
	import ctypes
	
	try:
		libc = ctypes.CDLL('libc.dylib', use_errno=True)
	except OSError:
		# We may be running afoul of OSX 10.11 System Integrity Protection.
		# Try by full and real pathname
		libc = ctypes.CDLL('/usr/lib/libSystem.dylib', use_errno=True)
	mach_absolute_time = libc.mach_absolute_time
	mach_timebase_info = libc.mach_timebase_info
	nanosleep		   = libc.nanosleep
	
	class mach_timebase_info_t(ctypes.Structure):
		_fields_ = [ ('numer', ctypes.c_uint32), ('denom', ctypes.c_uint32) ]
	
	class timespec(ctypes.Structure):
		_fields_ = [ ('tv_sec', ctypes.c_long), ('tv_nsec', ctypes.c_long) ]
	
	# set return type to match that of the function (ctypes assumes int32)
	mach_absolute_time.restype = ctypes.c_uint64
	# set the argument type to match that of the function
	mach_timebase_info.argtypes = [ctypes.POINTER(mach_timebase_info_t)]
	nanosleep.argtypes = [ctypes.POINTER(timespec), ctypes.POINTER(timespec)]
	
	# fetch timebase info to calculate the multiplier/divider factor
	tb_info = mach_timebase_info_t()
	retval = mach_timebase_info(ctypes.pointer(tb_info))
	if retval != 0:
		raise RuntimeError("Failure calling mach_timebase_info - return code %d" % retval)
	
	dividerSecs	  = 1e9	 * tb_info.denom / tb_info.numer
	dividerNanos  =		   tb_info.denom / tb_info.numer
	dividerMicros = 1000 * tb_info.denom / tb_info.numer
	
	def time():
		return mach_absolute_time() / dividerSecs
	
	def timeNanos():
		return mach_absolute_time() / dividerNanos
	
	def timeMicros():
		return mach_absolute_time() / dividerMicros
		
	def sleep(t):
		if t<=0:
			return
		ts = timespec()
		ts.tv_sec = int(t)
		ts.tv_nsec = int((t % 1) * 1000000000)
		retval = nanosleep(ctypes.pointer(ts), None)
		if retval:
			raise InterruptedException("Signal interrupted sleep")
	
	_bind(time, timeNanos, timeMicros, sleep)



def _Linux_init(raw=False):
	"""\
	Sets functions that retrieves time based on system monotonic timer.
	
	For Linux this is based on clock_gettime (CLOCK_MONOTONIC)
	or CLOCK_MONOTONIC_RAW if argument raw=True
	"""
	import ctypes
	
	# copied from linux/time.h
	CLOCK_MONOTONIC = 1
	CLOCK_MONOTONIC_RAW = 4
	
	if raw:
		CLOCK = CLOCK_MONOTONIC_RAW
	else:
		CLOCK = CLOCK_MONOTONIC
	try:
		librt = ctypes.CDLL('librt.so.1', use_errno=True)
	except OSError:
		librt = ctypes.CDLL('libc.so', use_errno=True)
	clock_gettime = librt.clock_gettime
	clock_nanosleep = librt.clock_nanosleep

	class timespec(ctypes.Structure):
		_fields_ = [ ('tv_sec', ctypes.c_long), ('tv_nsec', ctypes.c_long) ]

	# set argument types of clock_gettime)
	clock_gettime.argtypes = [ctypes.c_int, ctypes.POINTER(timespec)]
	clock_nanosleep.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(timespec), ctypes.POINTER(timespec)]
	
	ts = timespec()
	tsp = ctypes.pointer(ts)
	
	def time():
		if clock_gettime(CLOCK, tsp) == 0:
			return ts.tv_sec + ts.tv_nsec * 1e-9
		else:
			errno_ = ctypes.get_errno()
			raise OSError(errno_, os.strerror(errno_))
	
	def timeNanos():
		if clock_gettime(CLOCK, tsp) == 0:
			return ts.tv_sec * 1000000000 + ts.tv_nsec
		else:
			errno_ = ctypes.get_errno()
			raise OSError(errno_, os.strerror(errno_))
	
	def timeMicros():
		if clock_gettime(CLOCK, tsp) == 0:
			return ts.tv_sec * 1000000 + ts.tv_nsec / 1000
		else:
			errno_ = ctypes.get_errno()
			raise OSError(errno_, os.strerror(errno_))
	
	def sleep(t):
		if t<=0:
			return
		ts = timespec()
		ts.tv_sec = int(t)
		ts.tv_nsec = int((t % 1) * 1000000000)
		retval = clock_nanosleep(CLOCK, 0, ctypes.pointer(ts), None)
		if retval:
			raise OSError(retval, os.strerror(retval))
			raise InterruptedException("Signal interrupted sleep")
	
	_bind(time, timeNanos, timeMicros, sleep)



def _Windows_init():
	"""\
	Sets functions that use windows HPET timers via QueryPerformanceCounter
	
	See: http://starship.python.net/crew/theller/ctypes/tutorial.html
	"""
	import ctypes
	from ctypes import WinDLL
	
	klib = ctypes.WinDLL('kernel32.dll')

	qpc = klib.QueryPerformanceCounter
	qpf = klib.QueryPerformanceFrequency
	
	cwt = klib.CreateWaitableTimerA
	swt = klib.SetWaitableTimer
	wfso = klib.WaitForSingleObject
	closeHandle = klib.CloseHandle
	
	HANDLE = ctypes.c_voidp
	DWORD = ctypes.c_int32
	LONG = ctypes.c_long
	LARGE_INTEGER = ctypes.c_int64
	LPVOID = ctypes.c_voidp
	LPCTSTR = ctypes.c_char_p
	BOOL = ctypes.c_int
	
	WAIT_ABANDONED = 0x00000000L
	WAIT_TIMEOUT = 0x00000102L
	WAIT_FAILED = 0xFFFFFFFF
	
	INFINITE=0xFFFFFFFF
	_SECOND=10000000
	
	class SECURITY_ATTRIBUTES(ctypes.Structure):
		_fields_ = [ ( "nLength", DWORD), ("lpSecurityDescriptor", LPVOID), ("bInheritHandle", BOOL) ]
		
		

	# set argument types
	qpc.argtypes = [ ctypes.POINTER(LARGE_INTEGER) ]
	qpf.argtypes = [ ctypes.POINTER(LARGE_INTEGER) ]
	cwt.argtypes = [ ctypes.POINTER(SECURITY_ATTRIBUTES), BOOL, LPCTSTR ]
	swt.argtypes = [ HANDLE, ctypes.POINTER(LARGE_INTEGER), LONG, LPVOID, LPVOID, BOOL ]
	wfso.argtypes = [ HANDLE, DWORD ]
	closeHandle.argtypes = [ HANDLE ]
	
	# set return types
	# qpc.restype = BOOL
	# qpf.restype = BOOL
	cwt.restype = HANDLE
	swt.restype = BOOL
	wfso.restype = DWORD
	closeHandle.restype = BOOL
	
	
	freq = (ctypes.c_int64(0))

	if not qpf(ctypes.pointer(freq)):
		raise RuntimeError("Unable to call kernel32.dll QueryPerformanceFrequency. Cannot implement.")

	tmp = ctypes.c_int64()
	if not qpc(ctypes.pointer(tmp)):
		raise RuntimeError("Unable to call kernel32.dll QueryPerformanceCounter. Cannot implement.")
	
	def time():
		v=ctypes.c_int64()
		qpc(ctypes.pointer(v))
		return float(v.value) / freq.value
	
	def timeNanos():
		v=ctypes.c_int64()
		qpc(ctypes.pointer(v))
		return int((1000000000 * v.value) / freq.value)
	
	def timeMicros():
		v=ctypes.c_int64()
		qpc(ctypes.pointer(v))
		return int((1000000 * v.value) / freq.value)
	
	def sleep(t):
		if t<=0:
			return
		hTimer = cwt( None, False, None )
		if hTimer is None:
			raise RuntimeError("CreateWaitableTimer() failed. Cannot implement.")
		delay=LARGE_INTEGER(int(_SECOND * -t))
		success = swt(hTimer, ctypes.pointer(delay), 0, None, None, False)
		if not success:
			closeHandle( hTimer );
			raise RuntimeError("SetWaitableTimer() failed. Cannot implement.")
		retval = wfso( hTimer, INFINITE )
		closeHandle(hTimer)
		if retval == 0:
			return
		else:
			if retval == WAIT_ABANDONED:
				raise InterruptedException("Wait was abandoned")
			elif retval == WAIT_TIMEOUT:
				raise TimeoutError("Timeout")
			elif retval == WAIT_FAILED:
				raise RuntimeError("Wait failed")
			else:
				raise RuntimeError("Unknown error codde from WaitForSingleObject(): "+str(retval))
		
	
	_bind(time, timeNanos, timeMicros, sleep)


def _bind(*funcs):
	"""\
	Bind functions to be the module functions, and copy the documentation from
	the stub functions. Matches up by the name of the function
	""" 
	for func in funcs:
		name=func.__name__
		
		original=globals()[name]
		
		func.__doc__ = original.__doc__
		
		globals()[name]=func
	
	
import platform
import re

cygwin_version_regex=re.compile("^CYGWIN_NT-([0-9]+[.][0-9]+)")

p=platform.system()

if p=="Darwin":
	_Darwin_init()

elif p=="Linux":
	_Linux_init()

elif p=="Windows":
	_Windows_init()
	
elif cygwin_version_regex.match(p):
	match=cygwin_version_regex.match(p)
	version=float(match.group(1))
	if version >= 5.0:
		_Windows_init()
	else:
		raise NotImplementedError("Not implemented on this version of windows on cygwin, require nt 5.0 or higher. Platform string is '%s'" % p)
else:
	raise NotImplementedError("Not implemented for platform '%s'" % p)


if __name__=="__main__":
	print "This is a module library. Does nothing when run."
	
