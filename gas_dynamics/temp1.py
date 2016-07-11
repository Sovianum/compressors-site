import pandas as pd
import os.path
from compressor_engine import start_functions

data_dir = os.path.join(os.getcwd(), 'results', 'mean_radius_calculation')
file_path = os.path.join(data_dir, 'file_1.pkl')

data_chunk = pd.read_pickle(file_path)
compressor = data_chunk.compressor.values[0]

start_functions.do_profiling()
