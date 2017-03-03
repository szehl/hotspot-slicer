# Hotspot Slicer: Slicing virtualized Home Wi-Fi Networks for Air-Time Guarantee and Traffic Isolation
## 0. What is the Hotspot Slicer?
Nowadays,  the  usage  of  multiple  virtual  wireless
networks  on  top  of  one  physical  AP  is  very  common  in  home
Wi-Fi  networks.  Be  it  Hotspots  of  Internet  Service  Providers
(ISPs) or Mobile Network Operators (MNOs) used for offloading
their  traffic,  community  networks  or  plain  so-called  ”Guest-
Networks”. Whereas the home user (AP owner) in the best case
should not even be aware that his network connection is shared.
Most  of  the  ISPs  and  MNOs  are  now  trying  to  convince  their
customers to install an additional virtual wireless hotspot network
on  their  home  AP  and  offer  them  in  return  the  free  usage  of
all  other  available  hotspots.  But,  currently  most  costumers  are
skeptical  as  the  providers  cannot  guarantee  a  downlink  slice  of
air-time or real separation in time on the wireless access network.
In this repository, we hold the code for our demonstrator which is using a novel downlink slicing
scheme applied on commercial off-the-shelf hardware. Slicing
on MAC level can be applied to truly guarantee a fixed amount
of   air-time   for   the   home   user   and   provide   complete   traffic
separation  in  time  between  the  home  and  the  hotspot  network.
Moreover, our demonstrator shows the benefits of the approach
by comparing the quality of a high definition video stream with
and without our MAC slicing approach.

## 9. Contact
* Sven Zehl, TU-Berlin, zehl@tkn
* Anatolij Zubow, TU-Berlin, zubow@tkn
* Adam Wolisz, TU-Berlin, wolisz@tkn
* tkn = tkn.tu-berlin.de

