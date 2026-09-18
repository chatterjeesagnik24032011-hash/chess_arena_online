class MoveReview:
    LABELS = ["BOOK MOVE", "BEST MOVE", "BRILLIANT MOVE", "GREAT MOVE", "EXCELLENT MOVE", "GOOD MOVE", "INACCURACY", "MISTAKE", "BLUNDER"]

    def __init__(self):
        self.items = []

    def add_analysis(self, data):
        self.items.append(data)

    def undo_last(self, count=1):
        for _ in range(count):
            if self.items:
                self.items.pop()

    def counts(self):
        return {name: sum(item.get("label") == name for item in self.items) for name in self.LABELS}

    def average_loss(self):
        values = [max(0.0, float(item.get("loss", 0))) for item in self.items]
        return sum(values) / len(values) if values else 0.0

    def accuracy(self):
        # A transparent local estimate. Chess.com's exact accuracy formula is proprietary.
        values = [max(0.0, float(item.get("loss", 0))) for item in self.items]
        if not values:
            return 100.0
        return max(0.0, min(100.0, 100.0 - sum(min(v, 500) for v in values) / (len(values) * 10)))
