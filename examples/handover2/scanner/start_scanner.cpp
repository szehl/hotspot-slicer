#include <iostream>
#include <fstream>
#include <cstdio>
#include <set>
#include <string>
#include <tins/tins.h>
#include <boost/bimap.hpp>
#include <boost/circular_buffer.hpp>
#include "boost/tuple/tuple.hpp"
#include <boost/shared_ptr.hpp>
#include <execinfo.h>
#include <signal.h>

using namespace Tins;
using namespace boost::bimaps;


void handler(int sig) {
    void *array[10];
    size_t size;

    // get void*'s for all entries on the stack
    size = backtrace(array, 10);

    // print out all the frames to stderr
    fprintf(stderr, "Error: signal %d:\n", sig);
    backtrace_symbols_fd(array, size, STDERR_FILENO);
    exit(1);
}

/*
 * Passive scanning of WiFi channels for unicast packets (data & mgmt frames) transmitted by STAs.
 * For each STA the received signal strength (dBm) is stored in a circular buffer of fixed size.
 *
 * @author Zubow
 */
class STASniffer {
public:
    STASniffer(bool debug = true, int circBuffSize = 10, const std::string &outFname = "/tmp/sta_map.dat", long maxAge = 5000, long updateInterval=100);

    void run(const std::string &iface);
    // write data to file
    void exportDataToFile();

private:
    typedef Dot11::address_type Dott11AddressType;
    // libtins callback function
    bool callback(PDU &pdu);

    // pair: timestamp, value
    typedef boost::tuple<long, int> TimeSigPair;
    // buffer of pairs
    typedef boost::circular_buffer<TimeSigPair> SigPowCbType;
    // smart pointer
    typedef boost::shared_ptr<SigPowCbType> SigPowCbTypePtr;
    // map which maps mac addresses to buffers
    typedef boost::bimap< std::string, SigPowCbTypePtr> LUT;
    typedef LUT::value_type pos;

    // create LUT
    LUT tbl;

    bool mDebug;
    int mCircBuffSize;
    long mMaxAge;
    std::string mOutFname;
    std::ofstream mOutFile;
    unsigned long mLastExport;
    long mUpdateInterval;
};

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// constructor
STASniffer::STASniffer(bool debug, int circBuffSize, const std::string &outFname, long maxAge, long updateInterval) {
    mDebug = debug;
    mCircBuffSize = circBuffSize;
    mOutFname = outFname;
    mMaxAge = maxAge;
    mOutFile.open(outFname, std::ofstream::out);
    mLastExport = 0;
    mUpdateInterval = updateInterval;
}

// export data to file
void STASniffer::exportDataToFile()
{
    // open file
    mOutFile.open(mOutFname);

    struct timeval time;
    gettimeofday(&time, NULL);
    unsigned long now = ((unsigned long)time.tv_sec * 1000) + time.tv_usec / 1000;

    std::cout <<  now << ": exportDataToFile called" << std::endl;

    for( LUT::left_const_iterator i = tbl.left.begin(), iend = tbl.left.end(); i != iend; ++i )
    {
        SigPowCbTypePtr cbstar = i->second;

        if (cbstar) {
            if (mDebug) {
                std::cout << "buff size for: " << i->first << " is " << cbstar->size() << std::endl;
            }

            // calc signal power average
            double aggr_val = 0;
            double mean_age = 0;
            int cnt = 0;
            for (int k=0; k<cbstar->size(); k++) {
                unsigned long time = (*cbstar)[k].get<0>();
                int value = (*cbstar)[k].get<1>();

                std::cout << "E: " << (now-time) << "\t" << i->first << "\t" << value << std::endl;
                if (time >= now - mMaxAge) { // todo
                    aggr_val += value;
                    mean_age += (now-time);
                    cnt++;
                }
            }
            if (cnt > 0) {
                aggr_val /= cnt;
                mean_age /= cnt;

                mOutFile << i->first << "," << aggr_val << "," << cnt << "," << mean_age << std::endl;

                if (mDebug) {
                    std::cout << "add line: " << i->first << "," << aggr_val << ", (cnt=" << cnt << ")" << std::endl;
                }
            } else {
                // timeout out
                //mOutFile << i->first << ",-200" << std::endl;

                if (mDebug) {
                    std::cout << "add ine: " << i->first << ",-200,0,-1" << std::endl;
                }

            }
        }
    }
    mOutFile.close();
}

// libtins
void STASniffer::run(const std::string &iface) {
    Sniffer sniffer(iface, Sniffer::PROMISC, "", true);
    sniffer.sniff_loop(make_sniffer_handler(this, &STASniffer::callback));
}

// libtins
bool STASniffer::callback(PDU &pdu) {

    // get current time
    struct timeval time;
    gettimeofday(&time, NULL);
    unsigned long micros = ((unsigned long)time.tv_sec * 1000) + time.tv_usec / 1000;

    try {
        const RadioTap* tap = pdu.find_pdu<RadioTap>();

        if (tap) {
            // Sniff dot11 packets sent by STA to AP
            const Dot11* dot11 = pdu.find_pdu<Dot11>();

            // only packets from STA to AP
            if (dot11) {

                Dott11AddressType addr1 = dot11->addr1();

                if (dot11->to_ds()) {

                    if (mDebug) {
                        std::cout << "Dot11 toDS: APaddr: " << addr1 << ",";
                    }

                    Dott11AddressType addr2;
                    // data?
                    const Dot11Data* dot11data = pdu.find_pdu<Dot11Data>();
                    if (dot11data) {
                        addr2 = dot11data->addr2();
                    }
                    // mgmt?
                    const Dot11ManagementFrame* dot11mgmt = pdu.find_pdu<Dot11ManagementFrame>();
                    if (dot11mgmt) {
                        addr2 = dot11mgmt->addr2();
                    }

                    if (dot11data == NULL && dot11mgmt == NULL) {
                        return true;
                    } else {
                        if (mDebug) {
                            std::cout << "STAaddr: " << addr2 << ",";
                        }
                    }

                    std::stringstream out;
                    out << addr2;
                    std::string macaddr = out.str();

                    LUT::left_iterator it = tbl.left.find(macaddr);

                    int sig_power = static_cast<int16_t>(tap->dbm_signal());

                    if (it == tbl.left.end()) {
                        // create new vector entry + insert into map
                        SigPowCbTypePtr cb_ptr(new SigPowCbType(mCircBuffSize));
                        tbl.insert( pos(macaddr, cb_ptr) );
                        it = tbl.left.find(macaddr);
                        assert (it != tbl.left.end());
                    }
                    // push back new value
                    SigPowCbTypePtr cbstar = it->second;
                    if (cbstar) {
                        cbstar->push_back(TimeSigPair(micros, sig_power));
                    }

                    if (mDebug) {
                        std::cout << static_cast<int16_t>(tap->rate()) << "," << static_cast<int16_t>(tap->dbm_signal()) << ",";
                        std::cout << unsigned(tap->length())  << "," << unsigned(tap->channel_freq()) << std::endl;
                    }
                }
            }
        }

    } catch (const std::exception& ex) {
    	std::cout << "An exception occurred: ignoring packet." << std::endl;
    } catch (const std::string& ex) {
    	std::cout << "An exception occurred: " << ex << " ignoring packet." << std::endl;
    } catch (...) {
    	std::cout << "An exception occurred; ignoring packet." << std::endl;
    }


    // export current to file
    try {
        if ( (micros - mLastExport) >= mUpdateInterval) {
        	exportDataToFile();
		mLastExport = micros;
	}
    } catch (int e) {
        std::cout << "failed to export:  " << e << std::endl;
    }

    return true;
}

// entry point
int main(int argc, char* argv[]) {
    signal(SIGSEGV, handler);   // install our handler

    //std::cout << "Usage: <mon-dev>" << std::endl;

    // By default, sniff mon2
    std::string interface = "mon2";

    std::string map_file;

    if(argc == 2) {
      interface = argv[1];
 	  map_file = "/tmp/sta_map_" + interface + ".dat";
    } else {
	   map_file = "/tmp/sta_map.dat";
    }

    std::cout << "Using <mon-dev>=" << interface << "; map file to " << map_file << std::endl;

    STASniffer sniffer(true, 10, map_file, 5000, 100);

    sniffer.run(interface);
}
