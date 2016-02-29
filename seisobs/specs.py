# -*- coding: utf-8 -*-
"""
Created on Sat Jan 30 14:09:33 2016

@author: derrick

Contains specs for seisan format taken from:
http://seis.geus.net/software/seisan/seisan.pdf appendix A
"""

import warnings
import obspy
import sys  

##### Define important line types for various objects

origin_lines = ['1', 'E', 'H']
pick_lines = ['4']
magnitude_lines = ['1', '4']

## magnitue type code key
mag_key = {'L':'ML', 'B':'MB', 'S':'MS', 'W':'MW', 'C':'MC', 'M':'M'}
weight_key = {0:1.0, 1:.75, 2:.5, 3:.25, 4:0.0, ' ':1.0}
amp_phases = ['IAML']

##### Spec Class

class Spec(object):
    """
    class for holding specs for different line types for nordic files.
    
    Parameters
    colspec : list 
        list of tuples that define start/stop position of field
    colname : list
        list of strings that correspond the the fields defined in colspec
    colformat : list
        list of format strings for python types in each field
    validate_method : function
        A validation method for the series created by seisobs.core.Sline,
        takes a series as input with indicies as colnames. Should raise 
        exceptions or warnings
    """
    def __init__(self, colspec, colname, colformat, validate_method):
        
        if not len(colspec) == len(colname) == len(colformat):
            msg = 'colspec, colname, and colformat must have same len'
            raise ValueError (msg)
        self.colspec = colspec
        self.colname = colname
        self.colformat = colformat
        self.validate = validate_method
    
    def __iter__ (self): # itter through zipped col info
        for sp, na, fo in zip(self.colspec, self.colname, self.colformat):
            yield sp, na, fo

###### Define formats

specs = {} # blank dict to stuff Spec objects in. Key is line type (str)

## format for line type 1 (event metadata)

cs1 = [(0,1), (1,5), (5,6), (6,8), (8,10), (10,11), (11,13), (13,15), (15,16),
       (16,20), (20,21), (21,22), (22,23), (23,30), (30,38), (38,43), (43,44), 
       (44,45), (45,48), (48,51), (51,55), (55,59), (59,60), (60,63), (63,67),
        (67,68), (68,71), (71,75), (75,76), (76,79), (79,80)]
cn1 = ['bla1', 'year', 'bla2', 'month', 'day', 'fixotime', 'hour', 'minute',
       'bla3', 'second', 'mod', 'distancecode', 'eventid', 'latitude', 'longitude',
       'depth', 'depthcode', 'locindicator', 'hypagency', 'numstations', 'rms', 
       'magnitude', 'magtype', 'magagency', 'magnitude2', 'mag2type', 'mag2agency',
       'magnitude3', 'mag3type', 'mag3agency', 'linetype']
cf1 = ['%-s', '%4d', '%s', '%2d', '%2d', '%1s', '%2d', '%2d', '%s', '%4.1f', '%1s',
       '%1s', '%1s', '%7.3f', '%8.3f', '%5.1f', '%1s', '%1s', '%-3s', '3d%', '%4.2f',
       '%4.1f', '%1s', '%3s', '%4.1f', '%1s', '%3s', '%4.1f', '%1s', '%3s', '%1s']

def validate1(ser):
    """
    Validation methods for linetype 1
    """
    if not set(cn1).issubset(ser.index):
        msg = 'series does not have correct indicies'
        raise ValueError(msg)
    validate_mag(ser)
    validate_lat_lon(ser)
    validate_utc(ser)
    validate_blanks(ser)
    validate_year(ser)
    
specs['1'] = Spec(cs1, cn1, cf1, validate1)

## Format for line type 3 (comment) and other lines that arent used
lines_not_used = ['2','5', '6', '7', '8', '9', 'A']

cs3 = [(0,79), (79,80)]
cn3 = ['comment', 'linetype']
cf3 = ['%s', '%s']

def validate3(ser):
    """
    validation params for linetype 3
    """
    pass # nothing to see here folks, move along
    
specs['3'] = Spec(cs3, cn3, cf3, validate3)
for ltype in lines_not_used:
    specs[ltype] = Spec(cs3, cn3, cf3, validate3)



## format for line type 4 (station mag, amps, phases, etc.)

cs4 = [(0,1), (1,6), (6,7), (7,8), (8,9), (9,10), (10,14), (14,15), (15,16),
       (16,17), (17,18), (18,20), (20,22), (22,28), (28,29), (29,33), (33,40),
        (40,41), (41,45), (45,46), (46,51), (51,52), (52,56), (56,60), (60,63),
        (63,68), (68,70), (70,75), (75,76), (76,79), (79,80)]
cn4 = ['bla1', 'station', 'instrumenttype', 'component', 'bla2', 'qualityindicator',
       'phaseid', 'weight', 'autoflag', 'firstmotion', 'bla3', 'hour', 'minute',
       'second', 'bla4', 'duration', 'amplitude', 'bla5', 'period', 'bla6', 'backazimuth',
       'bla7', 'phasevelocity', 'incidenceangle', 'azimuthresid', 'traveltimeresid',
       'weight2', 'distance', 'bla8', 'azimuth', 'linetype']
cf4 = ['%s', '%-5s', '%s', '%s', '%s', '%s', '%4s', '%d', '%s', '%s', '%s', '%2d',
       '%2d', '%6.2f', '%s', '%4d', '%f7.1', '%s', '%4.2f', '%s', '%5.1f', '%s',
       '%4.0f','%4.0f', '%3d', '%5.1f', '%2d', '%5.0f', '%s', '%3d', '%s']

def validate4(ser):
    if not set(cn4).issubset(ser.index):
        msg = 'series does not have correct indicies'
        raise ValueError(msg) 
    if ser.azimuth < 0 or ser.azimuth > 360:
        msg = 'invalid azimuth found in series'
        raise ValueError(msg)
    if len(ser.station.strip()) == 0:
        msg = 'No station field found in series'
        raise ValueError(msg)
    if len(ser.component.strip()) == 0:
        msg = 'No component field found in series'
        raise ValueError(msg)    
    validate_utc(ser, ymd=False)
    validate_blanks(ser)

specs['4'] = Spec(cs4, cn4, cf4, validate4)

## format for line type E (hypoinverse error estimates)

cse = [(0,1), (1,5), (5,8), (14,20), (24,30), (30,32), (32,38), (38,43), (43,55),
       (55,67), (68,79), (79,80)]
cne = ['bla1', 'textgap', 'azgap', 'otimeerror', 'latitudeerror', 'bla2', 
       'longitudeerror', 'deptherror', 'covariancexy', 'covariancexz', 
       'covarianceyz', 'linetype']
cfe = ['%s', '%4s', '%3d', '%6.2f', '%6.1f', '%1s', '%6.1f', '%5.1f', '%12.4E',
       '%12.4E', '%12.4E', '%1s']

def validatee(ser):
    if not set(cne).issubset(ser.index):
        msg = 'series does not have correct indicies'    
        raise ValueError(msg)

specs['E'] = Spec(cse, cne, cfe, validatee)

## format for line type H (high accuracy hypocenter line)

csh = [(0,1), (1,5), (5,6), (6,8), (8,10), (10,11), (11,13), (13,15), (15,16),

       (16,22), (22,23), (23,32), (32,33), (33,43), (43,44), (44,52), (52,53),
        (53,59), (59,79), (79,80)]
cnh = ['bla1', 'year', 'bla2', 'month', 'day', 'fixotime', 'hour', 'minute', 
       'bla2', 'second', 'bla3', 'latitude', 'bla4', 'longitude', 'bla5', 'depth',
       'bla6', 'rms', 'bla7', 'linetype']
cfh = ['%-s', '%4d', '%s', '%2d', '%2d', '%1s', '%2d', '%2d', '%s', '%6.3f', 
       '%s', '%9.5f', '%s', '%10.5f', '%s', '%8.3f', '%s', '%6.3f', '%s', '%s']

validateh = validate1

specs['H'] = Spec(csh, cnh, cfh, validateh)

## formate for line type I (ID line)

csi = [(0,1), (1,8), (8,11), (11,12), (12,26), (26,27), (27,30), (30,35),(35,42),
       (42,56), (56,57), (57,60), (60,74), (74,75), (75,77), (77,79), 
        (79,80)]
cni = ['bla1', 'actionhelp', 'action', 'bla2', 'actiondatetime', 'bla3', 
       'textophelpoperator', 'operator', 'texthelpstatus',
       'statusflag', 'bla5', 'IDtext', 'ID', 'newflag', 'lock',  
       'bla6', 'linetype']
cfi = ['%s', '%-7s', '%-3s', '%s', '%-14s', '%1s', '%3s', '%5s', '%7s','%13s', 
       '%1s', '%3s', '%14s', '%1s', '%1s', '%3s', '%1s']

def validatei(ser):
    validate_blanks(ser)
    try:
        utc = obspy.UTCDateTime(ser.ID)
    except (ValueError, TypeError):
        msg = 'The following ID found in line is not a utcdatetime %s' % ser.ID
        raise ValueError(msg)

specs['I'] = Spec(csi, cni, cfi, validatei)

## format for line type 0 (blank and skip)

cs0 = [(0,78), (78,79)]
cn0 = ['bla1', 'linetype']
cf0 = ['%-s', '%1s']

def validate0(ser):
    validate_blanks(ser)
    
specs['0'] = Spec(cs0, cn0, cf0, validate0)

## formate for line type F (fault plane solution)

csf = [(0,10), (10,20), (20,30), (30,35), (35,40), (40,45), (45,50), (50,55),
       (55,60), (60,62), (62,63), (63,65), (66,69), (70,77), (77,78), (78,79),
        (79,80)]
cnf = ['strike', 'dip', 'rake', 'strikeerror', 'diperror', 'rakeerror', 'fiterror',
       'stationdistratio', 'amplituderatio', 'numbadpolarity', 'unused', 
       'numbadamplitudes', 'agency', 'program', 'quality', 'bla2', 'linetype']
cff = ['%10.0f', '%10.0f', '%10.0f', '%5.1f', '%5.1f', '%5.1f', '%5.1f', '%5.1f', 
       '%5.1f', '%2d', '%s', '%2d', '%-3s', '%-7s', '%1s', '%1s' ,'%1s']

def validatef(ser):
    validate_blanks(ser)
    if ser.strike > 360 or ser.strike < 0:
        msg = '%d is an invalid strike' % ser.strike
        raise ValueError(msg)
    if ser.dip > 90 or ser.dip < 0:
        msg = '%d is an invalid dip' % ser.dip
    if abs (ser.rake) > 180:
        msg = '%d is an invalid rake (-180 to 180)' % ser.dip

specs['F'] = Spec(csf, cnf, cff, validatef)


######## misc functions
def validate_utc(ser, ymd=True, hms=True):
    ds1 = ['year', 'month', 'day']
    ds2 = ['hour', 'minute', 'second']
    if ymd:
        if not set(ds1).issubset(ser.index):
            msg = 'Series does not have all %s' % str(ds1)
            raise ValueError(msg)
    if hms:
        if not set(ds2).issubset(ser.index):
            msg = 'Series does not have all %s' % str(ds2)
            raise ValueError(msg)
            
    utc = obspy.UTCDateTime(year=2015, month=01, day=15)
    try:
        if ymd:
            utc.year = ser.year
            utc.month = ser.month
            utc.day = ser.day
        if hms:
            if ser.hour < 0 or ser.hour > 48:
                raise ValueError('Hour must be between 0 and 48')
            utc.minute = ser.minute
            utc.second = int(ser.second)
            utc += ser.second - int(ser.second)
    except (ValueError, TypeError), e:
        msg = 'Invalid time value found in series, %s' % e
        raise ValueError(msg)

def validate_lat_lon(ser):
    ll = ['latitude', 'longitude']
    if not set(ll).issubset(ser.index):
        msg = 'Series does not have all %s' % str(ll)
        raise ValueError(msg)
    if abs(ser.latitude) > 90:
        msg = '%f is an invalid latitude value' % ser.latitude
        raise ValueError(msg)
    if abs(ser.longitude) > 180:
        msg = '%f is an invalid longitude value' % ser.longitude
        raise ValueError(msg)        

def validate_mag(ser):
    if not 'magnitude' in ser.index:
        msg = 'Series does not have magnitude in its index'
        raise ValueError(msg)
    if not ser.magnitude < 10.0:
        msg = 'mag is probably wrong (>10), else God help us all'
        raise ValueError(msg)

def validate_blanks(ser):
    blanks =('bla%d' % d for d in xrange(1, 12))
    for blank in blanks:
        if blank in ser.index:
            blastr = ser[blank].strip()
            if len(blastr) > 0:
                msg = '%s was found in blank string on series' % blastr
                raise ValueError(msg)
        else: # blanks are sequential, if we reach the end get off the train
            return

def validate_year(ser):
    if int(ser.year) < 1910:
        msg = 'Year reported before 1910, not allowed'
        raise ValueError(msg)
            

####### Class for string conversions to appropriate types

string_converters = {} # a cache of string converter instances
def get_string_converter(fmtstr): 
    """
    Function to get an isntance of StringConverter if one is already cached,
    or define an new one and cache it for future use
    Parameters
    ----------
    fmtstr : str
        A format string with the % syntax, valid examples are: %02f, %d, %s
    Returns
    --------
    An instance of StringConverter
    """
    if fmtstr in string_converters:
        return string_converters[fmtstr]
    else: 
        string_converters[fmtstr] = StringConverter(fmtstr)
        return string_converters[fmtstr]

  
class StringConverter(object):
    """
    Class for converting between strings and other data types given a format
    string. Example format strings are:
    %02f, %d, %s, etc. 
    Should generally be instantiated with the get_string_converter function
    Note
    -------
    l is a special character intrepreted by StringConverter that is a float
    without a decimal. So, '%4.2l' % 4 = 0400, this is used by some 
    hypoinverse formats.
    """
    accepted_chars = {'f':float, 's':str, 'd':int, 'e':float, 'l':float, 
                      'E':float}
    def __init__(self, fmtstr):
        self.fmtstr = fmtstr
        self._check_input(fmtstr)
        self.type, self.char = self._get_type(fmtstr)
        self.str2obj = _get_str2obj(self, fmtstr)
        if self.char == 'l': # replace l with f for operations
            self.fmtstr = self.fmtstr.replace('l', 'f')
        
    def obj2str(self, obj):
        """
        Given an object return use fmtstr to convert to str
        """
        try:
            strout = self.fmtstr % obj
            if self.char == 'l':
                strout = strout.replace('.', '')
            return strout
        except TypeError:
            msg = (('Input type and fmtstr charcter dont match, they are: '
                    ' %s and %s ' %(type(obj), self.type)))
            raise TypeError(msg)
        
    def _check_input(self, fmtstr): # make sure inputs are kosher, else raise
        if not isinstance(fmtstr, str):
            msg = 'fmt str argument is not a string, only strings are accepted'
            raise TypeError(msg)
        if not fmtstr.count('%') == 1:
            msg = (('There must be exactly one percent sign in the format '
                    'string %s doesnt have it') % fmtstr)
            raise ValueError(msg)
        if not any([x in fmtstr for x in self.accepted_chars]):
            msg = (('No supported formats found in fmtstr, they are %s') %
                    self.accepted_chars)
            raise ValueError(msg)
        if sum([fmtstr.count(x) for x in self.accepted_chars]) > 1:
            msg = (('Exactly one format character is required in fmtstr, you '
                    'passed %s') % fmtstr)
            raise ValueError(msg)
        if fmtstr.count('.') > 1:
            msg = 'fmtstr can only have one decimal, you passed %s' % fmtstr
            raise ValueError(msg)
            
    
    def _get_type(self, fmtstr): # return expected type for input
        for cha in self.accepted_chars:
            if cha in fmtstr:
                return self.accepted_chars[cha], cha
        

        
    def __str__(self):
        return self.fmtstr
    
    def __repr__(self):
        return 'StringConvert object, fmtstr = %s' % self.fmtstr
    
    def __call__(self, arg, strip_decimal=False):
        """
        Determine what output is needed by the type of the input. It it is a 
        str then call str2obj, else call obj2str
        
        Parameters
        ---------
        arg : int, float, str
            The input argument
        strip_decimal : bool
            If true strip the decimal in the string rep before returning
        """
        if isinstance(arg, str) and self.type == str: # str 2 str
            return self.str2obj(self, arg)
        elif isinstance(arg, self.type):
            return self.obj2str(arg)
        else:
            return self.str2obj(self, arg)
            
def _get_str2obj(strcnvr, fmtstr):
    """
    Take a string format and build function that will transform from str
    back to original data type (IE inverse of string format)
    """    
    # if the type is string return string caster
    if strcnvr.type == str: 
    
        def str2obj(coninst, obj):
            
            full_str = (coninst.fmtstr % obj)
            stripped_str = full_str.strip()     
            if len(obj) > len(stripped_str):
                return stripped_str
            else:
                return full_str
            try:
                return str(obj)
            except TypeError:
                msg = 'str2obj takes exatly one string, you passed %s' % type(obj)
                raise TypeError(msg)
            return str(obj)
            
        return str2obj
    # strip out char and % to look for decimal
    modstr = fmtstr.replace('%', '').replace(strcnvr.char, '')
    if '.' in modstr and strcnvr.char == 'l':
        strcnvr.divisor = 10**int(modstr.split('.')[1])
    else:
        strcnvr.divisor = 1
        
    def str2obj(coninst, obj):
        try:
            return coninst.type(obj)/coninst.divisor
        except TypeError:
            msg = 'str2obj takes exatly one string, you passed %s' % type(obj)
            raise TypeError(msg)
        except ValueError:
            if coninst.type == float or coninst.type == int and len(obj.strip()) == 0:
                return coninst.type(0)
    return str2obj   