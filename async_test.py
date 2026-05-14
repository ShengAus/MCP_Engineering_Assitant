import asyncio
import time

async def worker(i):
    print(f"worker {i} started")
    sleep_task = asyncio.create_task(asyncio.sleep(6))
    print(f"worker {i} do next ")
    await asyncio.sleep(2)
    await sleep_task
    print(f"worker {i} finished")
    return "result"

async def main():
   start = time.perf_counter()
   workers = [worker(i) for i in range(2)]
   results = await asyncio.gather(*workers)
   print(results)
   print("Total time:", round(time.perf_counter() - start, 2))

asyncio.run(main())