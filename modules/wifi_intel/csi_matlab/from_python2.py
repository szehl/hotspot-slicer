import matlab.engine
import numpy as np

eng = matlab.engine.start_matlab()
csi_trace = eng.read_bf_file('../fast_ch1')
csi_entry = csi_trace[100]
csi = eng.get_scaled_csi(csi_entry)
data = eng.squeeze_csi_data(csi)

mat = np.array(data._data).reshape(data.size[::-1]).T

csi_ant_1 = mat[:,0]
csi_ant_2 = mat[:,1]
csi_ant_3 = mat[:,2]

print(csi_ant_1)
print(csi_ant_2)
print(csi_ant_3)
