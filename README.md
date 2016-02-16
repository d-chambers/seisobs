
# Intro
Seisobs is a simple python package to read seisan s-files, in [Nordic format](http://seis.geus.net/software/seisan/seisan.pdf#page=421) into obspy catalog objects. Once an Obspy Catalog is instantiated it can be saved to several useful formats, including quakeML. See the [obspy docs](https://docs.obspy.org/packages/autogen/obspy.core.event.html) for more details.

## Installation
Just run the setup script in the seisobs directory:
```bash
python setup.py install
```
or use pip and install from github:
```bash
pip install git+https://github.com/d-chambers/seisobs
```

## Quick Start
To read an entire directory of S files into one catalog object simply do:



```python
import seisobs
sfile_directory = 'TEST_'
cat = seisobs.seis2cat(sfile_directory)
```


```python
cat
```




    50 Event(s) in Catalog:
    1990-12-13T11:09:19.800000Z | +60.328,   +5.167 | 0.9 MC
    1993-09-29T22:25:48.600000Z | +18.066,  +76.451 | 6.3 MB
    ...
    2009-01-15T17:49:39.100000Z | +46.857, +155.154 | 6.9 MB
    2011-01-29T06:55:00.000000Z |  +0.000,   +0.000
    To see all events call 'print(CatalogObject.__str__(print_all=True))'



This should have taken about 20 seconds to read in 50 files. A bit slow so hopefully you don't have to read thousands of s-files very often.

To convert a directory of sfiles into a directory of quakeML files you can use the seis2disk function (seisobs.seis2disk). This is probably the best route to take if you need to convert a large number of files because seisobs loads, converts, and saves one file at time to avoid excessive memory usage. 

## How it works

Seisobs has two modules:

1. Core : where the heavy lifting is done and main classes are defined. 

2. Specs : where the fixed width file specifications are stored and a few helper classes defined.

In the seisobs.specs module each line type has instance of the seisobs.specs.Spec class. These are contained in the specs dictionary where each key is the linetype as a string. So for linetype 1:


```python
spec1 = seisobs.specs.specs['1']
```

There are a few important attributes of the class:
    1. colspecs : the start and stop line width for a field
    2. colname : a string to identify the field
    3. colformat : a format string (eg '%2d') that indicates expected field type
    4. validate : a function that takes a pandas series as input and raises errors if any invalid values are encountered
 
 for example:


```python
print ('colspecs\n')
print (spec1.colspec)
print ('\n')
print ('colnames\n')
print (spec1.colname)
print('\n')
print ('colformat\n')
print (spec1.colformat)

```

    colspecs
    
    [(0, 1), (1, 5), (5, 6), (6, 8), (8, 10), (10, 11), (11, 13), (13, 15), (15, 16), (16, 20), (20, 21), (21, 22), (22, 23), (23, 30), (30, 38), (38, 43), (43, 44), (44, 45), (45, 48), (48, 51), (51, 55), (55, 59), (59, 60), (60, 63), (63, 67), (67, 68), (68, 71), (71, 75), (75, 76), (76, 79), (79, 80)]
    
    
    colnames
    
    ['bla1', 'year', 'bla2', 'month', 'day', 'fixotime', 'hour', 'minute', 'bla3', 'second', 'mod', 'distancecode', 'eventid', 'latitude', 'longitude', 'depth', 'depthcode', 'locindicator', 'hypagency', 'numstations', 'rms', 'magnitude', 'magtype', 'magagency', 'magnitude2', 'mag2type', 'mag2agency', 'magnitude3', 'mag3type', 'mag3agency', 'linetype']
    
    
    colformat
    
    ['%-s', '%4d', '%s', '%2d', '%2d', '%1s', '%2d', '%2d', '%s', '%4.1f', '%1s', '%1s', '%1s', '%7.3f', '%8.3f', '%5.1f', '%1s', '%1s', '%-3s', '3d%', '%4.2f', '%4.1f', '%1s', '%3s', '%4.1f', '%1s', '%3s', '%4.1f', '%1s', '%3s', '%1s']


Names that start with bla indicate a blank field is expected (will raise value error if it isn't).
Next an instance of seisobs.core.Sline is initiated with takes a raw line from an s-file and classifies it, then uses the appropriate Spec instance to load the data into a pandas series. For example,


```python
example_line_1 = ' 1996  625 0337 31.0 L  61.689   3.259 15.0  TES 35 3.0 3.3LTES 3.0CTES 3.2LNAO1'
sline = seisobs.core.Sline(example_line_1)
sline
```




    bla1                  
    year              1996
    bla2                  
    month                6
    day                 25
    fixotime              
    hour                 3
    minute              37
    bla3                  
    second              31
    mod                   
    distancecode         L
    eventid               
    latitude        61.689
    longitude        3.259
    depth               15
    depthcode             
    locindicator          
    hypagency          TES
    numstations         35
    rms                  3
    magnitude          3.3
    magtype              L
    magagency          TES
    magnitude2           3
    mag2type             C
    mag2agency         TES
    magnitude3         3.2
    mag3type             L
    mag3agency         NAO
    linetype             1
    dtype: object



Seisobs.core.Seisob then does the heavy lifting of taking many of these series that contain data for each line type and tries to appropriate fill the catalog structure. There are still some bumps here, and seisobs doesn't support all the different types of comment lines yet, but the framework should be sufficient to expand the functionality. At this point I am looking for some people that might understand nordic and quakeML formats better than I do to help expand the functionality. 


## Gotchas
The s-file line that lists the phase and arrival time (nordic format, linetype 4) only has fields for station and component. The Obspy Pick class (obspy.core.event.Pick) has a waveform id (obspy.core.event.WaveformStreamID) that requires the network, station, location, and channel. Seisobs has several ways to deal with this, and tries each in this order:

1. Use the full nslc code if it is found in a comment line in the s-file. If more than one is found use the first. 
    
2. Use a station inventory (can be read from stationXML using obspy.read_inventory) and see if any of the stations match both the component and station. If more than one match then use the first. An Inventory object or path to such can be attached to the class upon instantiation using the 
    
3. Load the waveform from the path in the line[type 6 lines using obspy.read, then see if any streams have IDs that could match. If more than one is found use the first. 
    
4. Use the network code (default is 'UK' for unknown) and channel code (default is 'BH') that is set when creating the Seisob instance. This is a very bad option and only executed when all other methods fail. A user warning will also be raised if the Seisob instance has it verbose flag set to True.
    
If all else fails and method number 4 is used it is not likely the waveform id will be correct. I recommend attaching an Inventory with the inventory_object argument of both seis2cat and seis2disk as it will be the most sure, and fastest, method for getting the waveform ID info.

## Running the tests
The tests are in py.test. You can run them simply by typing the following in a terminal (not python) when your cwd is set to the seisobs directory:
```bash
py.test
```
or 
```bash
py.test test_seisobs.py
```

It is that simple. 

## Seisobs in obspy?

I hope to submit a pull request to merge seisobs into the seisan module of obspy but there are several obstacles:

1. Pep 8: I have a few lines that go past the limit of 79 chars. I prescribe to the "beyond pep8" ideas Raymond Hettinger presented in [his 2015 pycon talk](https://www.youtube.com/watch?v=wf-BqAjZb8M) but I am happy to wrap some lines to meet obspy line width limits.

2. Doc Strings: I used the [google style doc string style](http://sphinxcontrib-napoleon.readthedocs.org/en/latest/example_google.html) rather than the reST style because it looks better in [spyder](https://github.com/spyder-ide/spyder), the IDE  I use. These will need to be changed, but this shouldn't take too long.  

3. I used the py.test framework rather than nose for all the automated tests. This is a bigger problem because I have never used nose (I am just getting my feet wet with py.test) so I may need some help with this one. 

4. I used pandas extensively because the DataFrame and Series are very powerful and convenient containers. Pandas is not currently a required dependency of obspy so I would need to rewrite large chunks of the code to stick within current dependencies. I am not very excited about doing this but I may if I get some extra time.  

5. I am not sure if it is Python 3 compatible.  This should be easy to check but I haven’t done so yet. 

6. Seisobs needs more general testing on a larger number of s-files than just those included in the test directory of seisan. 

## Catalog object to seisan?

I think that seisobs should be able to write s-files (nordic) but I don't have much time to code it right now.



```python

```
