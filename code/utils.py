
def add_dict(*dicts: dict) -> dict:
    keys = set()
    for dct in dicts:
        keys.update(dct.keys())
    
    new_dict: dict = {k: 0 for k in keys}
    
    for dct in dicts:
        for key, val in dct.items():
            if not isinstance(val, int) and not isinstance(val, float):
                raise TypeError(f'Expected int or float, not {type(val)}')
            new_dict[key]+=val
            
    return new_dict