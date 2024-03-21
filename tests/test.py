class foo:
    def __init__(self) -> None:
        self.a = 1
        
    def baz(self) -> None:
        print('fizz')
        
class bar:
    def __init__(self) -> None:
        self.b = 2
        
    def qux(self) -> None:
        print('qux')
        
class fred:
    def __init__(self) -> None:
        self.c = 3
        
    def quod(self) -> None:
        print('quod')
        
class waldo(foo, bar, fred):
    def __init__(self) -> None:
        for i in range(1, len(type(self).__mro__)-1):
            type(self).__mro__[i].__init__(self)


w = waldo()

w.baz()
w.qux()
w.quod()

print(w.a + w.b + w.c)