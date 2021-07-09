import dictdiffer


class History(list):

    def __init__(self, root, capacity=50):
        super().__init__()
        self.root = root
        self.capacity = capacity
        self.current_index = 0
        self.ignore_changes = False

    def add_entry(self, delta):
        if self.ignore_changes:
            return
        del self[:self.current_index]
        self.insert(0, delta)
        self.current_index = 0
        if self.capacity > 0:
            del self[self.capacity:]

    def undo(self):
        if self.current_index == len(self):
            return self.current_index
        delta = self[self.current_index]
        self.ignore_changes = True
        dictdiffer.revert(delta, self.root, in_place=True)
        self.ignore_changes = False
        self.current_index += 1
        return self.current_index

    def redo(self):
        if self.current_index == 0:
            return self.current_index
        self.current_index -= 1
        delta = self[self.current_index]
        self.ignore_changes = True
        dictdiffer.patch(delta, self.root, in_place=True)
        self.ignore_changes = False
        return self.current_index
