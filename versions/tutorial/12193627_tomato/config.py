from itertools import product

imths = [10, 20, 30, 40, 50]
mmths = [10, 20, 30, 40, 50]

CONFIG = [{"imth": imth, "mmth": mmth}
          for imth, mmth in product(imths, mmths)]