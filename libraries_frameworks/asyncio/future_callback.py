import asyncio

def on_done(fut: asyncio.Future):
    if fut.cancelled():
        print("Future was cancelled!")
    elif fut.exception():
        print("Future raised exception:", fut.exception())
    else:
        print("Future result:", fut.result())

async def worker(fut: asyncio.Future):
    await asyncio.sleep(1)
    fut.set_result("Hello from worker")

async def main():
    loop = asyncio.get_running_loop()
    fut = loop.create_future()

    # Register callback
    fut.add_done_callback(on_done)

    # Run the worker that will complete the future
    await worker(fut)

    # Wait to ensure callback runs
    await asyncio.sleep(0.1)

asyncio.run(main())
