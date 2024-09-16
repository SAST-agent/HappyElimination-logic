import random
import sys


def write_to_judger(msg: str) -> None:
    """
    按照4+N协议将消息输出给评测机

    :param msg: 需要输出的消息
    :type msg: str
    """
    sys.stdout.buffer.write(
        int.to_bytes(len(msg), length=4, byteorder="big", signed=False)
    )
    sys.stdout.buffer.write(msg.encode())
    sys.stdout.buffer.flush()


while 1:
    write_to_judger(
        f'{random.randint(0, 20)} {random.randint(0, 20)} {random.randint(0, 20)} {random.randint(0, 20)}')
