import matlab.engine
eng = matlab.engine.start_matlab()
#x = eng.read_bf_file('../fast_ch1')
csi = eng.get_nitem('../fast_ch1', 100)

