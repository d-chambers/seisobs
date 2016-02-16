# -*- coding: utf-8 -*-
"""
Created on Sat Jan 30 13:19:23 2016

@author: derrick
Py.test test framework for seisan2obspy code
"""
import pytest
import os
import seisobs
import ipdb
import obspy
import shutil
from builtins import str as text

##### module vars

test_dir = 'TEST_'

### misc functions

def walkdir(directory, ext):
    """
    Simple function to walk a directory and yield abs paths to each file if 
    the file has a given extension
    """
    for root, dirs, files in os.walk(directory, topdown=False):
        for fil in files:
            if ext in fil:
                path = os.path.abspath(root)
                yield os.path.join(path, fil)



###### test seis2disk
file_to_save1 = os.path.join('TEST_', '2000', '02', '01-1242-20L.S200002')
file_to_save2 = os.path.join('TEST_', '2005', '10', '23-2001-05L.S200510')
file_to_save3 = os.path.join('TEST_', '2009', '01', '15-1748-56D.S200901')

@pytest.yield_fixture(scope='module')
def setup_directory_to_save():
    seiob = seisobs.core.Seisob()
    for fts in [file_to_save1, file_to_save2, file_to_save3]:
        npath = fts.replace('TEST_', 'TEST2_')
        ndir = os.path.dirname(npath)
        if not os.path.exists(ndir):
            os.makedirs(ndir)
        shutil.copy2(fts, npath)
    seiob.seis2disk('TEST2_', savedir='DelXML')
    yield
    shutil.rmtree('TEST2_')
    shutil.rmtree('DelXML')

def test_directory_from_seis2disk(setup_directory_to_save):
    for fts in [file_to_save1, file_to_save2, file_to_save3]:
        assert os.path.exists(fts)
    cat = obspy.core.event.Catalog()
    for xml in walkdir('DelXML', '.xml'):
        cat += obspy.readEvents(xml)
    assert isinstance(cat, obspy.core.event.Catalog)
    assert len(cat) > 0

#### test inventory to get wid
file_to_test_inv = os.path.join('TEST_', '2005', '10', '23-2001-05L.S200510')
stas = ['STOK', 'STOK1', 'STOK2', 'MELS', 'MOR8', 'NSS', 'LOF', 'MOL', 'SUE']
nets = ['UU']
chas = ['BHZ', 'BHE', 'BHZ']

@pytest.fixture()
def get_inventory(): # make fake inventory for stations found in file
    networks = []
    for net in nets:
        sta_list = []
        for sta in stas:
            cha_li = []
            for cha in chas:
                chdi = {}
                chdi['latitude'] = 50.22
                chdi['longitude'] = -108.78
                chdi['elevation'] = 1000
                chdi['code'] = cha
                chdi['location_code'] = ' '
                chdi['depth'] = 0
                chan1 = obspy.station.Channel(**chdi)
                cha_li.append(chan1)
            stdi = {}
            stdi['channels'] = cha_li
            stdi['code'] = sta
            stdi['latitude'] = 50.22
            stdi['longitude'] = -108.78
            stdi['elevation'] = 1000            
            station = obspy.station.Station(**stdi)
            sta_list.append(station)
        nedi = {}
        nedi['code'] = net
        nedi['stations'] = sta_list
        network = obspy.station.Network(**nedi)
        networks.append(network)
    inventory = obspy.station.Inventory(networks=networks, source='Made_Up')
    return inventory

def test_inventory_get_wid(get_inventory):
    inv = get_inventory
    so = seisobs.core.Seisob(inventory_object=inv)
    cat = so.seis2cat(file_to_test_inv)
    for pick in cat[0].picks:
        wid = pick.waveform_id
        assert wid.network_code in nets
        assert wid.station_code in stas
        assert wid.channel_code in chas
    #assert 


#### End to End tests

####### test catalogs

cattars = ['events']

@pytest.fixture(scope='module')
def get_cat():
    return seisobs.core.seis2cat(test_dir)

@pytest.yield_fixture(scope='module')
def create_blank_directory():
    dirname = 'Delete_me'
    yield dirname
    if os.path.exists(dirname):
        shutil.rmtree(dirname)

class Test_S2OB_catalog:
    def test_type(self, get_cat):
        cat = get_cat
        assert isinstance(cat, obspy.core.event.Catalog) 
        assert len(cat) > 1
    def test_no_sfiles(self, create_blank_directory):
        with pytest.raises(ValueError):
            seiob = seisobs.Seisob()
            seiob.seis2cat(create_blank_directory)
            
######## test events

@pytest.fixture(scope='module')
def return_events(get_cat):
    events = []
    for event in get_cat:
        events.append(event)
    return events

@pytest.fixture(scope='module')
def return_event_comments(get_cat):
    comments = []
    for event in get_cat:
        for comment in event.comments:
            comments.append(comment)
    return comments

class Test_S2OB_events():
    def test_type(self, return_events):
        eves = return_events
        for eve in eves:
            assert isinstance(eve, obspy.core.event.Event)
    def test_attrs(self, return_events):
        eves = return_events
        attrs = ['origins', 'magnitudes', 'event_descriptions']
        for eve in eves:
            for attr in attrs:
                assert hasattr(eve, attr)
            assert len(eve.event_descriptions) > 0
    
class Test_S2OB_event_comments:
    def test_type(self, return_event_comments):
        for com in return_event_comments:
            assert isinstance(com, obspy.core.event.Comment)
    def test_length(self, return_event_comments):
        for com in return_event_comments:
            assert isinstance(com.text, text)
            assert len(com.text) > 0      
    
######## test origins
    
@pytest.fixture(scope='module')
def return_origins(return_events):
    origins = []
    for event in return_events:
        for origin in event.origins:
            origins.append(origin)
    return origins

class Test_S2OB_origins():
    def test_type(self, return_origins):
        origins = return_origins
        for origin in origins:
            assert isinstance(origin, obspy.core.event.Origin)
    def test_lat_lon(self, return_origins):
        origins = return_origins
        for origin in origins:
            assert abs(origin.longitude) <= 180
            assert abs(origin.latitude) <= 90
            assert abs(origin.latitude) <= 90
            assert abs(origin.longitude) <= 180
    def test_has_creation_info(self, return_origins):
        origins = return_origins
        for origin in origins:
            assert origin.creation_info is not None
    def test_has_quality_info(self, return_origins):
        origins = return_origins
        for origin in origins:
            assert hasattr(origin, 'quality')
    
########### test Arrivals
    
@pytest.fixture(scope='module')
def return_arrivals(return_events):
    arrivals_lists = []
    for event in return_events:
        for origin in event.origins:
            for arr in origin.arrivals:    
                arrivals_lists.append(arr)
    return arrivals_lists

class Test_S2OB_arrivals:
    def test_type(self, return_arrivals):
        assert len(return_arrivals) > 0
        for ar in return_arrivals:
            assert isinstance(ar, obspy.core.event.Arrival)
    def test_get_pick_from_id(self, return_arrivals):
        for ar in return_arrivals:
            pick_id = ar.pick_id
            pick = pick_id.getReferredObject()
            assert isinstance(pick, obspy.core.event.Pick)
            
#####  test picks
        
@pytest.fixture(scope='module')
def return_picks(return_events):
    picks = []
    for event in return_events:
        for pick in event.picks:
            picks.append(pick)
    return picks
    
class Test_S2OB_Picks():
    def test_type(self, return_picks):
        for pick in return_picks:
            assert isinstance(pick, obspy.core.event.Pick)
    
    def test_time(self, return_picks):
        for pick in return_picks:
            assert hasattr(pick, 'time')
            assert isinstance(pick.time, obspy.UTCDateTime)
    
    def test_eval_mode(self, return_picks):
        allowed_vals = ("manual", "automatic")
        for pick in return_picks:
            assert hasattr(pick, 'evaluation_mode')
            assert isinstance(pick.evaluation_mode, text)
            assert pick.evaluation_mode in allowed_vals
    
    def test_phase_hint(self, return_picks):
        for pick in return_picks:
            assert hasattr(pick, 'phase_hint')
            assert isinstance(pick.phase_hint, text)
    
    def test_polarity(self, return_picks):
        allowed_vals = ("positive", "negative", "undecidable")
        for pick in return_picks:
            assert hasattr(pick, 'polarity')
            assert isinstance(pick.polarity, text)
            assert pick.polarity in allowed_vals
    
    def test_onset(self, return_picks):
        allowed_vals = ("emergent", "impulsive", "questionable")
        for pick in return_picks:
            assert hasattr(pick, 'onset')
            assert isinstance(pick.onset, text)
            assert pick.onset in allowed_vals        
            
    def test_waveform_id(self, return_picks):
        for pick in return_picks:
            assert hasattr(pick, 'waveform_id')
            assert isinstance(pick.waveform_id, obspy.core.event.WaveformStreamID)
            assert len(pick.waveform_id.channel_code) == 3 # chan code is 3 chars
            
g1 = ' 1996 1021 2359 59.0 L  61.689   3.259 15.0  TES 35 3.0 3.3LTES 3.0CTES 3.2LNAO1'
g4 = ' FOO  SZ IS       2401 10.01                              70   -1.2710 95.1  95 '
@pytest.fixture()
def setup_seperate_day():
    so = seisobs.core.Seisob()
    s1 = seisobs.core.Sline(g1)
    s4 = seisobs.core.Sline(g4)
    return so, s4.sseries, so._get_utc(s1.sseries) 

def test_get_pick_time_different_day(setup_seperate_day):
    so, s4, utc1 = setup_seperate_day
    utc4 = so._get_pick_time(s4, utc1)
    assert utc4 > utc1
    assert utc4.day == utc1.day + 1
    

######## test magnitudes

@pytest.fixture(scope='module')
def return_magnitudes(return_events):
    magnitudes = []
    for event in return_events:
        for mag in event.magnitudes:
            magnitudes.append(mag)
    return magnitudes

class Test_S2OB_Magnitudes:
    def test_length(self, return_magnitudes):
        assert len(return_magnitudes) > 0
    def test_type(self, return_magnitudes):
        for mag in return_magnitudes:
            assert isinstance(mag, obspy.core.event.Magnitude)
    def test_mnag_is_float(self, return_magnitudes):
        for mag in return_magnitudes:
            assert isinstance(mag.mag, float)
    def test_mtypes(self, return_magnitudes):
        mk_vals = seisobs.specs.mag_key.values()
        for mag in return_magnitudes:
            assert isinstance(mag.magnitude_type, text)
            assert mag.magnitude_type in mk_vals
    # make sure blank lines didnt make it into magnitude list
    def test_no_defualts(self, return_magnitudes): 
        for mag in return_magnitudes:
            assert not (mag.creation_info.agency_id is None and mag.mag == 0.0)
    
####### test amplitudes

@pytest.fixture(scope='module')
def return_amplitudes(return_events):
    amplitudes = []
    for amplitude in return_events.amplitudes:
        amplitudes.append(amplitude)
    return amplitudes

############# Test read lines
## Linetype 1 tests
# good line 11
gl11 = ' 1996  625 0337 31.0 L  61.689   3.259 15.0  TES 35 3.0 3.3LTES 3.0CTES 3.2LNAO1'
gl12 = ' 2004  7 5 1809 36.9 L  57.505   7.139 15.0FFDNK  5 1.0 2.2LDNK 1.9CDNK        1'
# bad line 11, too few characters
bl11 = ' 1996  625 0337 31.0 L  61.689  3.259 15.0  TES 35 3.0 3.3LTES 3.0CTES 3.2LNAO1'
# bad line 12 wrong terminator code (doesnt exist), raises KeyError
bl12 = ' 1996  625 0337 31.0 L  61.689   3.259 15.0  TES 35 3.0 3.3LTES 3.0CTES 3.2LNAOR'
# bad line 13 wrong terminator code (valid but wrong)
bl13 = ' 1996  625 0337 31.0 L  61.689   3.259 15.0  TES 35 3.0 3.3LTES 3.0CTES 3.2LNAOH'
# bad line 14 invalid lat/lon
bl14 = ' 1996  625 0337 31.0 L  99.689   3.259 15.0  TES 35 3.0 3.3LTES 3.0CTES 3.2LNAO1'

## Linetype 4 tests
gl41 = ' FOO  SZ IS        337 56.01                              70   -1.2710 95.1  95 '
gl42 = ' MOL  SZ IP        338  6.15  248                         50    0.8310  244  64 '
gl43 = ' LFGH EE  IAML    1315 51.74       337.3 0.04                          0.12 171 '


## line 3, 6, 7 tests
gl31 = '     327.2      62.0     -11.2     0                                           3'
gl61 = ' 1996-06-25-0337-20S.NNSN__039                                                 6'
gl62 = ' LFE  EZ IP   1 D 0000 00.60                              20   0.01019 3.42  96'
gl71 = ' STAT SP IPHASW D HRMM SECON CODA AMPLIT PERI AZIMU VELO AIN AR TRES W  DIS CAZ7'

# line type E
gle1 = ' GAP=348        5.75     999.9   999.9999.9 -0.5178E+08 -0.1439E+09  0.5088E+09E'

# line type I
gli1 = ' ACTION:UP  14-02-26 21:02 OP:jh   STATUS:               ID:19960603195540     I'
gli2 = ' ACTION:HIN 16-02-02 12:01 OP:DC   STATUS:               ID:20160202141513     I'

# line type F
glf1 = '      94.0      32.0     -62.0  9.0 15.0  6.0  0.0  0.1           SMR FPFIT    F'

# good lines (shouldn't raise anything by passing all validations)
gls = [gl11, gl41, gl42, gl31, gl61, gl71, gle1, gli1, gli2]
@pytest.fixture(scope='module', params=gls)
def get_good_lines(request):
    return request.param

# badlines, raises ValueError
blv = [bl11, bl13, bl14]
@pytest.fixture(scope='module', params=blv)
def get_bad_value_lines(request):
    return request.param

# badlines, raises KeyError
blk = [bl12]
@pytest.fixture(scope='module', params=blk)
def get_bad_key_lines(request):
    return request.param

class TestSLines:
    def test_good_line11(self, get_good_lines):
        sline = seisobs.core.Sline(get_good_lines)
        assert isinstance(sline, seisobs.core.Sline)
    
    def test_bad_value_lines(self, get_bad_value_lines):
        with pytest.raises(ValueError):
            seisobs.core.Sline(get_bad_value_lines)

    def test_bad_key_lines(self, get_bad_key_lines):
        with pytest.raises(KeyError):
            seisobs.core.Sline(get_bad_key_lines)

############# Tests for StringConverter

bad_str_commands = ['%%02f', '%0dd', '%q ', '%.02.d']
good_str_commands = ['%0.2f', '%d', '%s', '%10d']
# list of tup for format, str_rep and object
cnvrt_str_list = [('%.2f', '1.00', 1.0), ('%2d', ' 1', 1), ('%s', 'bob', 'bob'),
                  ('%4.2l', '1000', 10.00), ('%-5s', 'b', 'b    ')]

@pytest.fixture(scope='module', params=bad_str_commands)
def get_bad_strcnv_params(request):
    return request.param
    
@pytest.fixture(scope='module', params=good_str_commands)
def get_good_strcnv_params(request):
    return request.param

@pytest.fixture(scope='module', params=cnvrt_str_list)
def get_convert_str_input_output(request):
    cs = seisobs.specs.get_string_converter(request.param[0])
    return (cs, request.param[1], request.param[2])

class Test_String_Converter:
    def test_bad_params(self, get_bad_strcnv_params):
        bs = get_bad_strcnv_params
        with pytest.raises(ValueError):
            seisobs.specs.StringConverter(bs)
    
    def test_good_params(self, get_good_strcnv_params):
        gs = get_good_strcnv_params
        sc = seisobs.specs.StringConverter(gs)
        assert isinstance(sc, seisobs.specs.StringConverter)
    
    def test_expected_input_output(self, get_convert_str_input_output):
        sc, string, obj = get_convert_str_input_output
        strip_decimal = False
        if sc.type == float:
            if '.' not in string:
                strip_decimal = True
        strout = sc(obj, strip_decimal)
        objout = sc(string)
        assert strout == string
        assert objout == obj