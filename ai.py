import random
import sys


def write_to_judger(msg: str) -> None:
    sys.stdout.buffer.write(
        int.to_bytes(len(msg), length=4, byteorder="big", signed=False)
    )
    sys.stdout.buffer.write(msg.encode())
    sys.stdout.buffer.flush()

while 1:
    write_to_judger(
        f'{random.randint(0, 19)} {random.randint(0, 19)} {random.randint(0, 19)} {random.randint(0, 19)}')
