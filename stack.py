# stack.py
class Stack:
    def __init__(self):
        self.stack = []
    
    def push(self, item):
        self.stack.append(item)
    
    def pop(self):
        if len(self.stack) == 0:
            return None
        return self.stack.pop()
    
    def peek(self):
        if len(self.stack) == 0:
            return None
        return self.stack[-1]
    
    def size(self):
        return len(self.stack)
    
    def is_empty(self):
        return len(self.stack) == 0
    
    def clear(self):
        self.stack = []
    
    def get_all(self):
        return list(self.stack)