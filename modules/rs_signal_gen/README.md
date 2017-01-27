# UniFlex R&S signal generator module

The R&S signal generator can be controlled from this module.

## Installation
To install UniFlex framework with all available modules, please go through all steps in [manifest](https://github.com/uniflex/manifests) repository.

Make sure that the folder bin/ is in global PATH variable:

    export PATH=~/repos/uniflex/modules/rs_signal_gen/bin:$PATH
    
or execute the Makefile in src/ when using a Python virtualenv

    cd src ; make
    
## Test the module

    cd test
    uniflex-agent --config config_local.yaml
