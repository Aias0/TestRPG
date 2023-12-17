test = 'thing'

match test:
    case x if x in ['thing', 'other thing']:
        print('1')
    case 'thing':
        print(2)
    
    case _:
        print(3)