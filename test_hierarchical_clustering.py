import numpy as np
import scipy.cluster.hierarchy as hac
import matplotlib.pyplot as plt

a = np.array([[0.1,   2.5],
              [1.5,   .4 ],
              [0.3,   1  ],
              [1  ,   .8 ],
              [0.5,   0  ],
              [0  ,   0.5],
              [0.5,   0.5],
              [2.7,   2  ],
              [2.2,   3.1],
              [3  ,   2  ],
              [3.2,   1.3]])

z = hac.linkage(a, method='single')
print z
