function y = squeeze_csi_date(csi)

y = mydb(abs(squeeze(csi).'));
