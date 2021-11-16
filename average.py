
class average:
    def __init__(self, size=14, error=10):
        self.itens = []
        self.size = size
        self.error = error
    def average(self, item = None, get_size = None):
        self.item = item
        self.flag = True
        if len(self.itens)==0 and self.item is not None:
            self.itens.append(self.item)
            self.flag = False
        if self.flag and self.item is not None and not (self.item>self.itens[-1]*(1+self.error/100)
                                                        or
                                                        self.item<self.itens[-1]*(1-self.error/100)):
            self.itens.append(self.item)
            if len(self.itens)>self.size:
                self.itens.pop(0)
        if self.itens == []:
            self.avg = 0
        elif get_size is not None:
            self.avg = (sum(self.itens[-get_size:])) / len(self.itens[-get_size:])
        else:
            self.avg = (sum(self.itens)) / len(self.itens)
        return self.avg