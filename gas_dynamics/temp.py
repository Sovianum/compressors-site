import numpy as np
import matplotlib.pyplot as plt
import os
import os.path

x = np.linspace(0, 2 * np.pi)
y = np.sin(x)

fig = plt.figure(figsize=(12, 10))
subplot = fig.add_subplot()
plt.plot(x, y)
plt.grid()
plt.savefig(os.path.join('images', 'test_plot.png'))
