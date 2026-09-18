import time
class ChessTimer:
    def __init__(self, minutes=10, increment=0):
        self.base=minutes*60; self.increment=increment; self.reset()
    def reset(self): self.white=self.base; self.black=self.base; self.last=time.monotonic(); self.running=True
    def update(self,turn):
        now=time.monotonic(); dt=now-self.last; self.last=now
        if self.running and turn is not None:
            if turn: self.white=max(0,self.white-dt)
            else: self.black=max(0,self.black-dt)
    def switch(self): self.last=time.monotonic()
    def add_increment(self,color):
        if color: self.white += self.increment
        else: self.black += self.increment
    def fmt(self,s): return f"{int(s)//60:02d}:{int(s)%60:02d}"
    def winner_by_time(self):
        if self.white<=0:return False
        if self.black<=0:return True
        return None
