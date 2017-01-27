function csi = get_nitem(fname, idx)

csi_trace = read_bf_file(fname);
csi_entry = csi_trace{idx};
csi = get_scaled_csi(csi_entry);
