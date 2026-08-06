import time


class MissionTimer:

    def __init__(self):

        self.start_time = None

        self.end_time = None


    def start(self):

        self.start_time = time.time()


    def stop(self):

        self.end_time = time.time()


    def elapsed(self):

        if self.start_time is None:

            return 0

        if self.end_time:

            return self.end_time - self.start_time

        return time.time() - self.start_time