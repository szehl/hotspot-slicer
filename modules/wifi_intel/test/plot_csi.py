import matplotlib.pyplot as plt
import pickle

import numpy as np

if __name__ == '__main__':

    file = open("csi_small.obj", 'rb')
    object_file = pickle.load(file)
    file.close()

    fig, ax = plt.subplots()
    for sample in range(20):
        rx1 = object_file[sample][0][0]
        rx2 = object_file[sample][0][1]
        rx3 = object_file[sample][0][2]

        v1 = 10*np.log10(np.square(np.absolute(rx1)))
        v2 = 10 * np.log10(np.square(np.absolute(rx2)))
        v3 = 10 * np.log10(np.square(np.absolute(rx3)))
        f = np.arange(0, 30, 1)

        ax.plot(f, v1, 'r-o', label='Rx1')
        ax.plot(f, v2, 'g-v', label='Rx2')
        ax.plot(f, v3, 'b-s', label='Rx3')

    #legend = ax.legend(loc='best', shadow=True)
    plt.grid(True)
    plt.xlabel('Subcarrier group (2 OFDM SC)')
    plt.ylabel('SNR [dB]')
    plt.title('Histogram of IQ')

    #plt.axis([0, 6, 0, 20])
    plt.show()