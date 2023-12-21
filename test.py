class test:
    def __init__(self) -> None:
        pass
    
class test2(test):
    def __init__(self) -> None:
        super().__init__()
        
        
print(test2().__format__())