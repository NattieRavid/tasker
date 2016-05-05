import worker
import time


task = worker.Task()

before = time.time()
task.apply_async_one(num=4)
for i in range(100):
    tasks = []
    for j in range(1000):
        task_obj = task.craft_task(num=5)
        tasks.append(task_obj)
    task.apply_async_many(tasks=tasks)
task.apply_async_one(num=6)
after = time.time()

print(after-before)
