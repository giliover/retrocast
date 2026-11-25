class Ring:
    """Fixed-size indexed history; lookup and append are constant time."""
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = [None] * capacity
        self.start = self.size = 0
    def append(self, value):
        self.data[(self.start+self.size)%self.capacity] = value
        if self.size == self.capacity:
            self.start = (self.start+1)%self.capacity
        else:
            self.size += 1
    def clear(self):
        self.data = [None]*self.capacity
        self.start = self.size = 0
    def __len__(self):
        return self.size
    def __getitem__(self, index):
        if isinstance(index,slice):
            return [self[i] for i in range(*index.indices(self.size))]
        if index < 0: index += self.size
        if not 0 <= index < self.size: raise IndexError(index)
        return self.data[(self.start+index)%self.capacity]
