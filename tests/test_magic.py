from enum import Enum, auto

class _shape(Enum):
    CIRCLE = auto()
    SQUARE = auto()
    TRIANGLE = auto()
    HEXAGON = auto()
    
class _runetype(Enum):
    TARGETING = auto()
    CARRIER = auto()
    
    ELEMENT = auto()
    MAGNITUDE = auto()
    
    INTEGRITY = auto()
    INVESTMENT = auto()
    
    IDENTITY =auto()
    
class _runeattribute(Enum):
    # TARGETING
        # TODO:
    
    # CARRIER
    BOLT = auto()
    BALL = auto()
    
    CONE = auto()
    WALL = auto()
    
    # ELEMENT
    FIRE = auto()
    WATER = auto()
    EARTH = auto()
    AIR = auto()
    
    LIGHTNING = auto()
    
    # Magnitude
    MINOR = auto()
    LESSER = auto()
    GREATER = auto()
    SUPERIOR = auto()
    SUPREME = auto()
        
    # INTEGRITY
    ORDER = auto()
    STABILITY = auto()
    INSTABILITY = auto()
    CHAOS = auto()
    
    # INVESTMENT
    ENCHANT = auto()
    BOON = auto()
    CURSE = auto()
    
    # IDENTITY
    SELF = auto()
    OTHER = auto()
    
    @staticmethod
    def attr_val(attr: Enum) -> int:
        d = {
            _runeattribute.MINOR: -10,
            _runeattribute.LESSER: -5,
            _runeattribute.GREATER: 5,
            _runeattribute.SUPERIOR: 10,
            _runeattribute.SUPREME: 15,
            
            _runeattribute.ORDER: 10,
            _runeattribute.STABILITY: 5,
            _runeattribute.INSTABILITY: -5,
            _runeattribute.CHAOS: -10,
        }
        if attr in d.keys():
            return d[attr]
        return None
    

class Rune:
    def __init__(
        self,
        name: str,
        cost: int,
        type: _runetype,
        attributes: list[_runeattribute],
        conflicts: dict[_runetype | _runeattribute, int] = {},
        restrictions: list[_runetype | _runeattribute] = [],
        base_strength: int = 0,
        base_integrity: int = 0,
    ) -> None:
        self.name = name
        self.cost = cost
        
        self.type = type
        if not isinstance(attributes, list):
            self.attributes = [attributes]
        self.attributes = attributes
        
        self.conflicts = conflicts
        self.restrictions = restrictions
        
        self.base_integrity = base_integrity
        self.base_strength = base_strength
        
    @property
    def integrity(self) -> int:
        t = self.base_integrity
        if self.type == _runetype.INTEGRITY:
            return t + _runeattribute.attr_val(self.attributes[0])
        return t
    
    @property
    def strength(self) -> int:
        t = self.base_strength
        if self.type == _runetype.MAGNITUDE:
            return t + _runeattribute.attr_val(self.attributes[0])
        return t
        

class Matrix:
    def __init__(self, name: str, cost: int, shape: _shape, base_integrity: int, restrictions: list[Rune] = [], base_strength: int = 0) -> None:
        self.name = name
        self.cost = cost
        self.shape = shape
        self.base_integrity = base_integrity
        self.restrictions = restrictions
        self.base_strength = base_strength
        

class Spell:
    def __init__(self, matrix: Matrix, runes: list[Rune], name: str | None = None):
        self.matrix = matrix
        self.runes = runes
        
        self._name = name
        
        self.fail_thresh = 0
        
    @property
    def name(self) -> str:
        if self._name is not None:
            return self._name
        
        name = ''
        element = [rune for rune in self.runes if rune.type == _runetype.ELEMENT]
        if element:
            name += f'{element[0].attributes[0].name.capitalize()}'
        
        carrier = [rune for rune in self.runes if rune.type == _runetype.CARRIER]
        if carrier:
            if element:
                name += ' '
            name+= f'{carrier[0].attributes[0].name.capitalize()}'
            
        return name
        
    
    @property
    def integrity(self) -> int:
        t = self.matrix.base_integrity
        for i, rune in enumerate(self.runes):
            if i > 0 and self.runes[i-1].type == _runetype.IDENTITY:
                t += rune.strength * _runeattribute.attr_val(self.runes[i-1].attributes[0])
            t += rune.integrity
        return t

    @property
    def strength(self) -> int:
        t = self.matrix.base_strength
        for i, rune in enumerate(self.runes):
            if i > 0 and self.runes[i-1].type == _runetype.MAGNITUDE:
                t += rune.strength * _runeattribute.attr_val(self.runes[i-1].attributes[0])
            else:
                t += rune.strength
        return t
    
    @property
    def cost(self) -> int:
        t = self.matrix.cost
        for rune in self.runes:
            t+= rune.cost
        return t
                
    @property
    def valid(self) -> bool:
        num_runes = len(self.runes)
        match self.matrix.shape:
            case _shape.CIRCLE:
                pass
            case _shape.TRIANGLE:
                if num_runes % 3 !=0:
                    return False
            case _shape.SQUARE:
                if num_runes % 4 != 0:
                    return False
            case _shape.HEXAGON:
                if num_runes %6 != 0:
                    return False
                
        for rune in self.runes:
            if rune in self.matrix.restrictions:
                return False
            
            if [k for k in rune.restrictions if k in [j[0] if isinstance(j, list) else j for j in [x for xs in [(i.attributes, i.type) for i in self.runes if i != rune] for x in xs]]]:
                return False
            
        if self.runes[0].type != _runetype.CARRIER:
            return False
                
        if self.integrity < self.fail_thresh:
            return False
        

        return True
    
    def cast():
        """ TODO cast spell here. """
        pass
    
    def __str__(self):
        _ = ''
        if not self.valid:
            _ = 'INVALID - '
        return f'{_}{self.name}: {self.matrix.name}{[_.name for _ in self.runes]} | {self.integrity} | <{self.cost}> [{self.strength}]'


fire_rune = Rune('Fire Rune', 10, _runetype.ELEMENT, [_runeattribute.FIRE], conflicts={_runeattribute.WATER: 25}, base_integrity=-10)
water_rune = Rune('Water Rune', 10, _runetype.ELEMENT, [_runeattribute.WATER], conflicts={_runeattribute.FIRE: 25}, base_integrity=-10)
bolt_rune = Rune('Bolt Rune', 2, _runetype.CARRIER, [_runeattribute.BOLT], restrictions=[_runetype.CARRIER], base_integrity=-10)

strength_rune = Rune('Strength Rune', 20, _runetype.MAGNITUDE, [_runeattribute.GREATER], base_integrity=-20)

triangle_matrix = Matrix('Triangular Matrix', 20, _shape.TRIANGLE, 100)

spell = Spell(triangle_matrix, [bolt_rune, strength_rune, fire_rune])

print(spell)
