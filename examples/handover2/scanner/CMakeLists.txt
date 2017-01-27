cmake_minimum_required(VERSION 2.8)
project(scanner)

FIND_PACKAGE(libtins QUIET)
FIND_PACKAGE(Threads QUIET)

IF(libtins_FOUND)
    SET(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/../)
    INCLUDE_DIRECTORIES(
        ${LIBTINS_INCLUDE_DIRS}
        ${PCAP_INCLUDE_DIR}
    )
    LINK_LIBRARIES(${LIBTINS_LIBRARIES})

    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

    set(SOURCE_FILES start_scanner.cpp)

    add_executable(scanner ${SOURCE_FILES})


ELSE(libtins_FOUND)
    MESSAGE(
        ERROR
        "Cannot build since libtins is not installed. "
        "Run cmake again once it is installed in order to compile them."
    )
ENDIF(libtins_FOUND)
