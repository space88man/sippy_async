import os
import socket
from sippy.Time.MonoTime import MonoTime
from anyio import (
    create_task_group,
    sleep,
    run,
    create_memory_object_stream,
    create_udp_socket,
)
import logging


STATE = {"UDP_ID": 0}

LOG = logging.getLogger("sippy-async")


class AsyncUDPServer:
    uopts = None
    stats = None
    qsend, qrecv = (None, None)
    id = None

    def __init__(self, global_config, uopts):
        self.uopts = uopts
        self.qsend, self.qrecv = create_memory_object_stream(256)
        self.id = STATE["UDP_ID"]
        self.stats = [0, 0, 0]
        STATE["UDP_ID"] += 1
        ED2.regServer(self)

    async def run(self):
        LOG.info(
            "UDP server starting: %d, %s", self.id, laddress := self.uopts.laddress
        )

        async with create_task_group() as self._tg:
            async with await create_udp_socket(
                local_host=laddress[0],
                local_port=laddress[1],
            ) as self.sock:
                self._tg.start_soon(self.handle_outgoing)
                async for packet, (host, port) in self.sock:
                    self.stats[2] += 1
                    # the callback expects [] around IPv6 literal addresses
                    if self.uopts.family == socket.AF_INET6:
                        host = "[" + host + "]"
                    try:
                        self.uopts.data_callback(packet, (host, port), self, MonoTime())
                    except Exception:
                        LOG.exception(
                            "Udp_server: unhandled exception when processing incoming data"
                        )

    def send_to(self, data, address):
        """Strip [] from IPv6 literal addresses"""

        if self.uopts.family == socket.AF_INET6:
            address = (address[0][1:-1], address[1])
        self.qsend.send_nowait((data, address))

    async def handle_outgoing(self):
        async with self.qrecv:
            async for item in self.qrecv:
                packet, (host, port) = item
                if isinstance(packet, str):
                    packet = packet.encode()
                await self.sock.sendto(packet, host, port)

    def shutdown(self):
        self._tg.cancel_scope.cancel()


class Cancellable:
    """Wrapper around a coroutine to allow
    cancellation.

    self._tg is set once the coroutine is scheduled
    and is used for cancellation.
    """

    def __init__(self, ed, task):
        self._task = task
        self.ed = ed
        self._tg = None

    def cancel(self):
        if self.ed.is_running:
            assert self._tg
            self._tg.cancel_scope.cancel()
        else:
            self.ed.tpending.remove(self)

    def go(self):
        self.ed.go_timer(self)

    async def run_task(self):
        async with create_task_group() as self._tg:
            return await self._task()


def _twrapper(ed, timeout_cb, ival, nticks, abs_time, *cb_params):
    async def _task():
        if abs_time:
            await sleep(max(ival - MonoTime(), 0.0))
        else:
            await sleep(ival)
        timeout_cb(*cb_params)

    return Cancellable(ed, _task)


class EventDispatcher3:
    def __init__(self, freq=100.0):
        self.is_running = False
        self.tpending = []
        self.servers = []
        self.tsend, self.trecv = (None, None)

    def go_timer(self, k):
        """Schedules a timer if the event loop is running;
        else just add it to a pending list.
        """

        if self.is_running:
            self.tsend.send_nowait(k)
        else:
            self.tpending.append(k)

    async def _timer_wait(self):
        """This coroutine is also used to signal to exit the loop.
        Just set self.inbox = None and set self._timer
        """

        async with self.trecv:
            async for item in self.trecv:
                if item is None:
                    break
                self.tg.start_soon(item.run_task)

    async def aloop(self):
        """Runs event loop forever."""

        # overloaded member: used to schedule timers
        # and exit the loop if self.inbox = None

        self.is_running = True
        self.tsend, self.trecv = create_memory_object_stream(256)

        async with create_task_group() as self.tg:
            # schedule pending timers
            while self.tpending:
                await self.tsend.send(self.tpending.pop())

            while self.servers:
                self.tg.start_soon(self.servers.pop().run)

            # this task runs the event loop forever...
            self.tg.start_soon(self._timer_wait)

    def loop(self):
        run(self.aloop, backend=os.getenv("SIPPY_ASYNC_BACKEND", "asyncio"))

    def regTimer(self, timeout_cb, ival, nticks=1, abs_time=False, *cb_params):
        timer = _twrapper(self, timeout_cb, ival, nticks, abs_time, *cb_params)
        return timer

    def regServer(self, obj):
        self.servers.append(obj)

    def breakLoop(self):

        self.is_running = False
        self.tg.cancel_scope.cancel()


ED2 = EventDispatcher3()
from sippy.Core import EventDispatcher

del EventDispatcher.ED2

EventDispatcher.ED2 = ED2

from sippy import Udp_server

Udp_server.Udp_server = AsyncUDPServer
