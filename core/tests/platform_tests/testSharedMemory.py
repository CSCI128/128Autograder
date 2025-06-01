import unittest
import multiprocessing.shared_memory as sm
import dill


class TestSharedMemory(unittest.TestCase):

    def test_serialization(self):
        sharedMemory = sm.SharedMemory(create=True, size=2 ** 20)

        data = dill.dumps(["some", "words" * 100, "in" * 1000, "here" * 50])

        sharedMemory.buf[:len(data)] = data

        sharedMemory.close()
        sharedMemory.unlink()
