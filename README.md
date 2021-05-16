# sippy-async

This is an experimental monkey patch for [sippy/b2bua](https://github.com/sippy/b2bua)
to run the event loop under async python using [anyio](https://github.com/agronholm/anyio).


## What is Sippy B2BUA (aka sippy)

This is a library for handling SIP messages as well as a framework
for scripting B2BUAs.
The architecture consists of  UDP servers in threads to handle network events,
and an event loop running in the main thread to handle the FSM for a B2BUA.

The event loop is a hand-crafted one based on [ElPeriodic](https://github.com/sobomax/libelperiodic).
The event loop supports time-based callbacks, as well as
scheduling callbacks from external threads.

### How do I run async python code then?
The simplest method is to let the sippy event loop run in the main thread
and run an async event loop in another thread.

## What does this module do?

This module monkey patches sippy so that the event loop is run by asyncio or trio via anyio.
You can use it to utilize the sippy framework in async python applications
and yet control the event loop yourself.

At this stage, the patched objects emulate enough methods to run simple B2BUA scripts.

Historical note: sippy used to be based on Twisted before migrating off that framework
to its own loop implementation.

### Get Started

```
# this must be the first thing imported in your application as it will
# monkey patch key sippy classes
import sippy_async

# your B2BUA script goes here.....
```


### Monkey Patch
What is patched?
* the event loop object: `sippy.Core.EventDispatcher.ED2` — this object is replaced
    with a duck-type equivalent. The async event loop is started in
    the `loop()` method; it also contains an async
    entrypoint `async def aloop()` if you want to start the event loop manually.
* the UDP server: `sippy.Udp_server.Udp_server` — this object is replaced to run
    on the async event loop instead of threads
	
What happened to `ED2.callFromThread()`? In sippy this method is used to schedule
SIP message handling callbacks in the main thread. With this monkey patch, there
is no need for this inter-thread cross-over and the callbacks are invoked directly.

If you are using threads you should use the standard trio/asyncio mechanisms for 
running code in the event loop.

### Tests

How do I run the `sippy.Time.Timeout` testsuite?

```
# monkey patches sippy.Core.EventDispatcher.ED2 -
# the key event loop object

import sippy_async
from sippy.Time import Timeout

Timeout.testTimeout()
Timeout.testTimeoutAbsMono()
```
How do I run the `sippy.Udp_server` testsuite?

```
# monkey patches Udp_server as well...

import sippy_async
from sippy.Udp_server import self_test

self_test.run()

```





