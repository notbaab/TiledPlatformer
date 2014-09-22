# A file containing various abstractions I have found useful over the years


class CStruct:
  """a C like struct class. Credit: http://stackoverflow.com/questions/35988/c-like-structures-in-python
  Ex: mystruct = CStruct(field1=value1, field2=value2)
      print(mystruct.field1)"""
  def __init__(self, **kwds):
    self.__dict__.update(kwds)
