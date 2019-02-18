# pyincore

**Pyincore** is a Python package to analyze and visualize various hazard (earthquake, tornado, hurricane etc.) 
scenarios developed by the Center for Risk-Based Community Resilence Planning team from NCSA. 
The development is part of NIST sponsored IN-CORE (Interdependent Networked Community Resilience Modeling 
Environment) initiative. Pyincore allows users to apply hazards on infrastructure in selected areas. 
Python framework acceses underlying data through local or remote services and facilitates moving 
and synthesizing results.
                      
**Pyincore** as a python module can be used to write hazard workflow tools.

## Installation

### Prerequisites

[Python 3.5](https://www.python.org) or greater

[GDAL](https://www.gdal.org) - Geospatial Data Abstraction Library

- **Linux** 

    **Pyincore** uses GDAL library which has to be installed separately for example by using `apt-get` package utility 
    on Debian, Ubuntu, and related Linux distributions.
    ```
    apt-get gdal
    ```
    Additonal information can be found  at the wiki page [How to install GDAL](https://github.com/domlysz/BlenderGIS/wiki/How-to-install-GDAL).
- **Windows**

    GDAL for Windows can be difficult to build, requiring a number of prerequisite software, libraries, and header files. 
    If you are comfortable building Windows software then building GDAL from source as a develop build is preferred.
    
    If you are not comfortable building GDAL then you may want to download the `gdal` binaries 
    from [Windows Binaries for Python](https://www.lfd.uci.edu/~gohlke/pythonlibs/). 
    The problem with this is that GDAL header files 
    are not included, so you cannot do a `pip install` of packages that want to utilize 
    the GDAL headers. Fiona and Rasterio will need binaries installed from this page as well, 
    and if you run into failed dependancies during the setup process you may want to revisit 
    the page and install the binaries for the Python extensions that are causing problems. 
    Additional information can be found at the wiki page [How to install GDAL](https://github.com/domlysz/BlenderGIS/wiki/How-to-install-GDAL).


**Optional**: `virtualenv` (available by running `pip install virtualenv`) or [Anaconda](https://www.anaconda.com/distribution/), 
note that a full Anaconda distribution will include Python, so installing Python first isn't needed if you use Anaconda

### All Platforms

1. Download or clone the source code from [NCSA Git](https://git.ncsa.illinois.edu/incore/pyincore) repository.
2. Change into the ```pyincore``` directory (or prepend the path to the directory onto files reference from here on out)
3. **Optional**: Activate your virtual or conda environment
4. From the terminal, in the project folder (pyincore) run:
    ```
    python setup.py install
    ```
5. Verify the installation
    ```
    python setup.py test
    ```

    **Windows specific installation notes**
    
    - Open the `Anaconda` prompt, or `cmd` depending on if you are using Anaconda or not before you activate 
    virtual environment (step 3 above)

    **Mac specific installation notes**

    - `spacialindex` library is needed, but appears to be included on other platforms. The easy way to install 
    is to use [Homebrew](https://brew.sh/), and run:
        ```
        brew install spacialindex
        ```
    - We use `matplotlib` library to create graphs. There is a Mac specific installation issue addressed at 
    StackOverflow [link1](https://stackoverflow.com/questions/4130355/python-matplotlib-framework-under-macosx) and 
    [link2](https://stackoverflow.com/questions/21784641/installation-issue-with-matplotlib-python). In a nutshell, 
    insert line:
        ```
        backend : Agg
        ```
        into `~/.matplotlib/matplotlibrc` file.

## Running

Verify the installation by running the test script
```
python setup.py test
```

## For developers

- Installation directly from `Git`:
    ```
    git clone https://git.ncsa.illinois.edu/incore/pyincore
    cd pyincore
    pip install -e
    ```
- **Pyincore documentation*** can be found on [Incore server](http://incore2.ncsa.illinois.edu/doc).
- ***Jupyter notebooks*** can be run interactively with [Jupyter](https://git.ncsa.illinois.edu/incore/pyincore).
- **Tests** In order to run Tests, you need to create a file called, `.incorepw` under tests folder. The file needs 
    two lines: `user name` in the 1st line and `password` in the 2nd line
- There is a known issue running analyses on multiple threads in some versions of 
    `python 3.6.x` running on `MacOS High Sierra 10.13.x`. If you see such errors on your environment, 
    set the following environment variable in your `.bash_profile` as a workaround: 
    ```
    export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
    ``` 
    Issue details can be found [here](http://sealiesoftware.com/blog/archive/2017/6/5/Objective-C_and_fork_in_macOS_1013.html)

## Data

To access data in the **Incore**, you must have an account recognized by `Incore Auth`, 
or a [free Incore ID](https://incore.ncsa.illinois.edu).

## Contributions
If you find a bug or want a feature, feel free to open an issue on [NCSA Jira](https://jira.ncsa.illinois.edu/login.jsp).

## Support
This work was performed under financial assistance award 70NANB15H044 from 
the National Institute of Standards and Technology (NIST) as part of 
the Interdependent Networked Community Resilience Modeling 
Environment [(IN-CORE)](http://resilience.colostate.edu/in_core.shtml).