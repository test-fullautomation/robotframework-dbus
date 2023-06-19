import queue

class PriorityQueue(queue.PriorityQueue):
   def __init__(self, type="FIFO"):
      super(PriorityQueue, self).__init__()
      self.counter = 0

      self.factor=-1
      if type=="LIFO":
         self.factor=-1
      elif type=="FIFO":
         self.factor=1
      else:
         raise Exception("Fatal Error: PriorityQueue type not allowed: '%s'!" % str(type))

   def put(self, item, priority=None):
      if priority==None:
         self.counter += 1
         priority=self.counter

      super(PriorityQueue, self).put((self.factor * priority, item), block=True)
