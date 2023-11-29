import signal

class GracefulExit:
  
    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)

    def should_exit(self):
        return self.kill_now
    
    def _exit_gracefully(self, *args):
        self.kill_now = True

if __name__ == '__main__':
    import time
    exiter = GracefulExit()
    while not exiter.should_exit():
        time.sleep(1)
        print("doing something in a loop ...")

    print("End of the program. I was killed gracefully :)")
