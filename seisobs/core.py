# -*- coding: utf-8 -*-
"""
Created on Sat Jan 30 13:13:36 2016

@author: derrick
functions to read a single S-file into a catalog object
"""

import obspy
import os
import seisobs
import pandas as pd
import warnings
from builtins import str as text

def seis2cat(sfile, authority='local', inventory_object=None, 
             default_network='UK', default_channel='BH', verbose=False):
    """
    Function to convert an s-file, or directory of s-files, to obspy catalog 
    object
    
    Parameters
    ---------
    sfile : str
        Path to an s-file (nordic format) or directory of s-files
    authority : str
        Default authority for resource IDs
    inventory_object : None, obspy.station.Inventory or path to such
        If not None, an inventory object or path to a file that is readable
        by obspy.read_station to use to obtain full NSLC codes. See docs string
        on Seisob._get_nslc for info on why this might be useful. 
    default_network : str
        The default network to use in resource IDs when the real network code
        is not recorded in the s-file or the inventory-object
    default_chan : str
        Two letter prefix to make channel code to proceed component for
        guessing at station codes
    verbose : bool
        If True print all user warnings, else suppress them
    
    Returns
    -------
    obspy.core.event.Catalog object
    """
    so = Seisob(**locals())
    cat = so.seis2cat(sfile)
    return cat

def seis2disk(sfile, sformat='quakeml', savedir='quakeml', ext='.xml',
              directory_struct='yyyy-mm', skip_if_exists=True, 
              authority='local', inventory_object=None, 
              default_network='UK', default_channel='BH', verbose=False):
    """
    Save a seisan s-file, or directory of s-files, in nordic format,
    to disk using obspy Catalog as intermediate step. Raises ValueError
    if no valid s-files are found.
    
    Parameters
    -----------
    sfile : str
        Path to the sfile or sdirectory
    sformat : str
        The format to use when saving files. Any obspy-supported format
        is fine. See obspy doc for details. 
    savedir : str
        seis2disk will save each S-file in a directory named savedir with
        the same structure as s-files (savedir-year-month). File names 
        will be yyyy-mm-ddThh-mm-ss based on utcdate time in first origin.
        Directory structure is controlled by the directory_structure arg.
    ext : str
        Extensions of file name if saving events
    directory_struct : str
        The structure of the subdirectories in savedir. Permitted values 
        are:
            yyyy-mm-dd : savedir/year/month/day/file
            yyyy-mm : savedir/year/month/file
            yyyy : savedir/year/file
            flat : savedir/file
    skip_if_exists : bool
        If a file already exists that the new file would be named, 
        guessing based on s-file name, then don't read file just continue
        to next
    authority : str
        Default authority for resource IDs
    inventory_object : None, obspy.station.Inventory or path to such
        If not None, an inventory object or path to a file that is readable
        by obspy.read_station to use to obtain full NSLC codes. See docs string
        on Seisob._get_nslc for info on why this might be useful. 
    default_network : str
        The default network to use in resource IDs when the real network code
        is not recorded in the s-file or the inventory-object
    default_chan : str
        Two letter prefix to make channel code to proceed component for
        guessing at station codes
    verbose : bool
        If True print all user warnings, else suppress them
    """
    so = Seisob(**locals())
    so.seis2disk(**locals())

##### seis2ob and supporting functions

class Seisob(object):
    """
    Main class for Seisobs
    
    Parameters 
    -----------
    authority : str
        Default authority for resource IDs
    inventory_object : None, obspy.station.Inventory or path to such
        If not None, an inventory object or path to a file that is readable
        by obspy.read_station to use to obtain full NSLC codes. See docs string
        on Seisob._get_nslc for info on why this might be useful. 
    default_network : str
        The default network to use in resource IDs when the real network code
        is not recorded in the s-file or the inventory-object
    default_chan : str
        Two letter prefix to make channel code to proceed component for
        guessing at station codes
    verbose : bool
        If True print all user warnings, else suppress them
    """
    def __init__(self, authority='local', inventory_object=None, 
                 default_network='UK', default_channel='BH', verbose=False,
                 **kwargs):
        self.authority = authority
        self.default_network = default_network
        self.verbose = verbose
        self.default_channel = default_channel
        self.df_cache = {}
        if isinstance(inventory_object, text):
            try:
                inventory_object = obspy.read_inventory(inventory_object)
            except (ValueError, IOError):
                msg = 'failed to read %s' % inventory_object
                raise ValueError(msg)
        if not isinstance(inventory_object, obspy.station.Inventory):
            self.inventory = None
        else:
            self.inventory = inventory_object 
            inv = self.inventory
            chans = [x.split('.') for x in inv.get_contents()['channels']]
            cols = ['network', 'station', 'location', 'channel']
            self.wid_df = pd.DataFrame(chans, columns=cols)
    
    def seis2cat(self, sfile, **kwargs):
        """
        Read a seisan s-file, or directory of s-files, 
        in nordic format and return an obspy catalog object. Raises ValueError
        if no valid s-files are found.
        
        Parameters
        -----------
        sfile : str
            Path to the sfile or sdirectory
        
        Returns
        -------
        Obspy.core.event.Catalog instance
    
        Notes
        ------
        http://seis.geus.net/software/seisan/seisan.pdf appendix A
        """
        cat = obspy.core.event.Catalog()
        if os.path.isdir(sfile):
            for sfi in self._get_sfil_from_dir(sfile):
                cat += self.seis2cat(sfi)
        elif os.path.isfile(sfile):
            try:
                sdf = self.load_sfile_into_df(sfile)
            except (ValueError, KeyError):
                msg = '%s is not a proper S-File' % sfile
                self.warn(msg)
                return obspy.core.event.Catalog()
            eve = self._load_event(sdf, sfile)
            cat.events.append(eve)
        if len(cat.events) == 0:
            msg = 'No valid s-files found, no events created'
            raise ValueError(msg)
        return cat
        
    def seis2disk(self, sfile, sformat='quakeml', savedir='quakeml', ext='.xml',
                  directory_struct='yyyy-mm', skip_if_exists=True, **kwargs):
        """
        Save a seisan s-file, or directory of s-files, in nordic format,
        to disk using obspy Catalog as intermediate step. Raises ValueError
        if no valid s-files are found.
        
        Parameters
        -----------
        sfile : str
            Path to the sfile or sdirectory
        sformat : str
            The format to use when saving files. Any obspy-supported format
            is fine. See obspy doc for details. 
        savedir : str
            seis2disk will save each S-file in a directory named savedir with
            the same structure as s-files (savedir-year-month). File names 
            will be yyyy-mm-ddThh-mm-ss based on utcdate time in first origin.
            Directory structure is controlled by the directory_structure arg.
        ext : str
            Extensions of file name if saving events
        directory_struct : str
            The structure of the subdirectories in savedir. Permitted values 
            are:
                yyyy-mm-dd : savedir/year/month/day/file
                yyyy-mm : savedir/year/month/file
                yyyy : savedir/year/file
                flat : savedir/file
        skip_if_exists : bool
            If a file already exists that the new file would be named, 
            guessing based on s-file name, then don't read file just continue
            to next
    
        """
        if os.path.isdir(sfile):
            for sfi in self._get_sfil_from_dir(sfile):
                self.seis2disk(sfi, sformat, savedir, ext, directory_struct)
        elif os.path.isfile(sfile):
            utc = self._get_utc_from_sfile_name(sfile)
            sname = self._get_save_name(utc, ext, directory_struct, savedir)
            if skip_if_exists and os.path.exists(sname):
                # If the sfile has been modified since the quakml still write
                qml_modtime = os.path.getmtime(sname)
                smodtime = os.path.getatime(sfile)
                if qml_modtime > smodtime:
                    return
            try:
                sdf = self.load_sfile_into_df(sfile)
            except ValueError:
                msg = '%s is not a proper S-File' % sfile
                self.warn(msg)
                return 
            eve = self._load_event(sdf, sfile)
            cat = obspy.core.event.Catalog(events=[eve])
            self._save_event(cat, utc, sformat, sname)

    def _get_utc_from_sfile_name(self, sfile):
        sp0, sp1 = os.path.basename(sfile).split('.S')
        udi = {}
        udi['day'] = int(sp0[:2])
        udi['hour'] = int(sp0[3:5])
        udi['minute'] = int(sp0[5:7])
        udi['second'] = int(sp0[8:10])
        udi['year'] = int(sp1[:4])
        udi['month'] = int(sp1[4:6])
        utc = obspy.UTCDateTime(**udi)
        return utc
    
    def _get_save_name(self, utc, ext, directory_struct, savedir):
        subdir = self._get_subdir(utc, directory_struct, savedir)
        if not os.path.exists(subdir):
            os.makedirs(subdir)
        filename = str(utc).split('.')[0].replace(':', '-') + ext
        return os.path.join(subdir, filename)
    
    def _save_event(self, cat, utc, sformat, sname):
        assert len(cat.events) == 1 # make sure only one event in cat
        #utc_rID = obspy.UTCDateTime(str(cat[0].resource_id))
        # make sure utc from file name and file are nearly the same
        #assert abs(utc_rID - utc) < 60# happens alot, not sure why
        cat.write(sname, sformat)

    def _get_subdir(self, utc, directory_struct, savedir):
        year = '%04d' % utc.year
        month = '%02d' % utc.month
        day = '%02d' % utc.day
        if directory_struct.lower() == 'yyyy-mm-dd':
            return os.path.join(savedir, year, month, day)
        elif directory_struct.lower() == 'yyyy-mm':
            return os.path.join(savedir, year, month)
        elif directory_struct.lower() == 'yyyy':
            return os.path.join(savedir, year)         
        elif directory_struct.lower() == 'flat':
            return savedir
        else:
            msg = 'directory_struct of %s not supported' % directory_struct
            raise ValueError(msg)
            
    def load_sfile_into_df(self, sfile):
        """
        Load the contents of a single sfile into a dataframe
        
        Parameters
        ----------
        sfile : str
            Path to a valid s-file
        
        Returns
        --------
        A DataFrame with columns of linetype and series
        """
        if sfile.split('.')[-1] == 'sebk':
            msg = '%s is a seisan backup file' % sfile
            raise ValueError(msg)
        df = pd.DataFrame(columns=['linetype', 'series'], dtype=object)
        with open(sfile, 'r') as sfile:
            for slnum, sline in enumerate(sfile):
                sli = sline.decode('utf-8').rstrip(os.linesep)
                if len(sline.rstrip()) < 1: # if blank line at end of file
                    continue
                try:
                    slin = Sline(sli, seiob=self)
                except (ValueError):
                    msg = '%s in %s is not a valid line, skipping' % (sline, sfile)
                    self.warn(msg)
                    continue
                df.loc[len(df)] = {'linetype':slin.slinetype, 'series':slin.sseries}
        self._validate_sdf(df, sfile)
        return df
    
    def _load_event(self, sdf, sfile):
        """
        Function to take the sdf (which contains all files read in) and create an
        event object
        """
        self.df_cache = {} # clear cache on new event
        evdi = {}
        
        magnitudes = self._get_magnitudes(sdf)
        picks, arrivals, amplitudes = self._get_picks_arrivals_amplitudes(sdf) 
        origins = self._get_origins(sdf, arrivals)
        # load various params
        evdi['picks'] = picks
        evdi['origins'] = origins
        evdi['magnitudes'] = magnitudes
        evdi['amplitudes'] = amplitudes   
        evdi['resource_id'] = self._gen_event_resource_id(sfile)
        evdi['comments'] = self.get_comments(sdf)
        evdi['event_descriptions'] = self._make_description(sdf)
        eve = obspy.core.event.Event(**evdi)
        # set preferred origin and magnitudes
        if len(origins):
            eve.preferred_origin_id = str(eve.origins[0].resource_id)
        if len(magnitudes):
            eve.preferred_magnitude_id = str(eve.magnitudes[0].resource_id)

        return eve
    
    def get_comments(self, sdf):
        sd3 = sdf2df(sdf, '3')
        comments = []
        for ind, row in sd3.iterrows():
            com = obspy.core.event.Comment(text=row.comment)
            comments.append(com)
        return comments

    def _gen_event_resource_id(self, sfile):
        # Generate event resource id based on time in first origin
        utc = self._get_utc_from_sfile_name(sfile)
        date_str = str(utc).split('.')[0].replace(':','-')
        resource_id = obspy.core.event.ResourceIdentifier(date_str)
        return resource_id

    ### Get origins
    def _get_origins(self, sdf, arrivals):
        """
        using the sdf get the origins
        """
        origins = []
        df1 = sdf2df(sdf, '1')
        dfe = sdf2df(sdf, 'E')
        dfi = sdf2df(sdf, 'I')
        for ind, row in df1.iterrows(): # assume Hypoinv reflects first line 1
            origin = self._origin_from_1line(ind, row, dfe, dfi, arrivals)
            origins.append(origin)
        return origins
    
    def _origin_from_1line(self, ind, row, dfe, dfi, arrivals):
        ordi = {} # init blank dict to stuff origin keyword params in
        # get specialized linetypes

        ordi['latitude'] = row.latitude
        ordi['longitude'] = row.longitude
        ordi['depth'] = row.depth
        ordi['time'] = self._get_utc(row)
        ordi['fixed_time'] = row.fixotime == 'F' or row.fixotime == 'f'
        ordi['creation_info'] = self._get_creation_info(row, dfi)
        ordi['quality'] = self._get_quality(row, dfe)
        ordi['arrivals'] = arrivals
        origin = obspy.core.event.Origin(**ordi)        
        if ind == 0: # if first line attach hyp errors to origin
            if len(dfe) > 0: # if there is a hyp line
                sse = dfe.iloc[0]
                lat_er = sse.latitudeerror
                lon_er = sse.longitudeerror
                dep_er = sse.deptherror
                origin.latitude_errors.latitude_error = lat_er
                origin.longitude_errors.longitude_error = lon_er
                origin.depth_errors.depth_error = dep_er    
        return origin
    
    def _make_description(self, sdf):
        df1 = sdf2df(sdf, '1')
        ser = df1.iloc[0] # assume first 1 line has correct info
        des = ser.distancecode + ser.eventid
        return [obspy.core.event.EventDescription(des)]
    
    def _get_creation_info(self, row, dfi):
        ci = {}
        ci['agency_id'] = row.hypagency
        if len(dfi) > 0: # using last action to guess this stuff
            se = dfi.iloc[0]
            ci['author'] = se.operator
            ci['creation_time'] = self._get_utc_from_I(se)
        creation = obspy.core.event.CreationInfo(**ci)
        return creation
    
    def _get_quality(self, ser1, dfe):
        qdi = {}
        qdi['standard_error'] = ser1.rms
        qdi['associated_phase_count'] = ser1.numstations        
        if len(dfe) > 0:
            qdi['azimuthal_gap'] = dfe.iloc[0].azgap
        oq = obspy.core.event.OriginQuality(**qdi)
        return oq
        
    ### Get picks
    def _get_picks_arrivals_amplitudes(self, sdf):
        """
        Function for parsing info from the #4 lines
        """
        df1 = sdf2df(sdf, '1') # checked that first line is one earlier
        utc1 = self._get_utc(df1.iloc[0]) # start time in line 1
        df4 = sdf2df(sdf, '4')
        picks = []
        arrivals = []
        amplitudes = []
        get_nslc_dict = self._nslc_method_prep(sdf)        
        for ind, row in df4.iterrows(): # iterate through all pick lines
            get_nslc_dict['ser4'] = row
            pick = self._get_pick(ind, row, get_nslc_dict, utc1)
            picks.append(pick)
            if not pick.phase_hint in seisobs.specs.amp_phases:
                arrival = self._get_arrival(ind, row, pick)
                arrivals.append(arrival)
            else:
                amplitude = self._get_amplitude(ind, row, pick)
                amplitudes.append(amplitude)
        return picks, arrivals, amplitudes
    
    def _get_pick(self, ind, row, get_nscl_dict, utc1):
        pidi = {} # pick dict (don't confuse with dic pic)
        pidi['evaluation_mode'] = "manual" if row.autoflag == ' ' else 'automatic'
        pidi['time'] = self._get_pick_time(row, utc1)
        pidi['phase_hint'] = row.phaseid
        pidi['polarity'] = self._get_polarity(row)
        pidi['onset'] = self._get_onset(row)
        # get waveform_id
        net, sta, loc, cha = self._get_nslc(get_nscl_dict)
        pidi['waveform_id'] = self._make_waveform_id(net, sta, loc, cha)
        pick = obspy.core.event.Pick(**pidi)
        return pick

    def _get_arrival(self, ind, row, pick):
        ardi = {}
        ardi['pick_id'] = pick.resource_id
        ardi['time_residual'] = row.traveltimeresid
        ardi['phase'] = pick.phase_hint
        ardi['azimuth'] = row.azimuth
        ardi['time_weight'] = seisobs.specs.weight_key.get(row.weight)
        arrival = obspy.core.event.Arrival(**ardi)  
        return arrival
    
    def _get_amplitude(self, ind, row, pick):
        amdi = {}
        amdi['generic_amplitude'] = row.amplitude
        amdi['period'] = row.period
        amplitude = obspy.core.event.Amplitude(**amdi)
        return amplitude

    def _get_nslc(self, dic):
        """
        Because seisan line 4 types only have station and component, a method
        for getting the network, full channel, and location code is needed
        _assign_wfid_method looks for the appropriate method and returns a
        function to perform the task. The order that methods are tried are:
        
        1. Use comment lines with "CHANNELID" to get codes
        2. Use station inventory attached to Seisob class
        3. Try loading the seisan file (waveform) and select the waveform
        4. Use station as component code and network attribute of seisob and
            loc = ' '. This will be wrong but it is as close as we can get. 
        """
        ser = dic['ser4']
        dic['seiob'] = self
        # try using comment lines
        if dic['scnldf'] is not None:
            try:
                return get_nslc_from_comment(**dic)
            except ValueError:
                msg = (('Comment lines with id exist but %s %s is not found' 
                       ) % (ser.station, ser.component))
                self.warn(msg)
         # try using station inventory     
        if dic['nslcdf'] is not None:
            try:
                return get_nslc_from_inventory(**dic)
            except ValueError:
                msg = (('Valid station inventory exist but %s %s is not found' 
                        ) % (ser.station, ser.component))
                self.warn(msg)
        # try loading waveform file to get info
        if dic['st'] is not None:
            try:
                return get_nscl_from_waveform(**dic)
            except ValueError:
                msg = (('Valid waveform file exist but %s %s is not in it') 
                        % (ser.station, ser.component))
        # everything has failed if you are here, fill in partial info
        msg = (('All other methods failed, filling in partial nslc for station'
                ' %s on component %s') % (ser.station, ser.component))
        self.warn(msg)
        return get_nscl_from_thin_air(**dic)
    
    def _nslc_method_prep(self, sdf):
        """
        Because seisan line 4 types only have station and component, a method
        for getting the network, full channel, and location code is needed. 
        This function stuffs the things the get_nscl functions will need into
        a dictionary to be passed as kwargs. A function done the line will
        determine which of the four (defined under misc section in core) to 
        use.

        """        
        out = {}
        scnldf = self._make_scnl_df(sdf)
        # Try using comment lines
        if len(scnldf) == 0: # if this seems to have failed
            scnldf = None
        # try using attached pick_id_object
        if isinstance(self.inventory, obspy.station.Inventory):
            nslcdf = self.wid_df
        else:
            nslcdf = None
        # try using waveform
        try: 
            st = self.load_sfile_stream(sdf)
        except (ValueError, IOError, AttributeError): 
            st = None             
        out['scnldf'] = scnldf
        out['nslcdf'] = nslcdf
        out['st'] = st
        out['network'] = self.default_network
        out['channel_prefix'] = self.default_channel
        return out
            
            
    def _make_scnl_df(self, sdf):
        # take a df with comment lines that have scnl and return dataframe
        sdf_cid = self._get_comments_with_str(sdf, 'CHANNELID')
        cols = ['station', 'channel', 'network', 'location']
        df = pd.DataFrame(columns=cols)
        for ind, row in sdf_cid.iterrows():
            com = row.series.comment.split(':')[1].rstrip()
            sta, cha, net, loc = [x.strip() for x in com.split('.')]
            ser = pd.Series([sta, cha, net, loc], index=cols)
            df.loc[len(df)] = ser
        return df
    
    def _get_onset(self, ser):
        if ser.qualityindicator.upper() == 'I':
            return "impulsive"
        elif ser.qualityindicator.upper() == 'E':
            return "emergent"
        else:
            return "questionable"
    
    def _get_polarity(self, ser):
        if ser.firstmotion.upper() == 'C':
            return 'positive'
        elif ser.firstmotion.upper() == 'D':
            return 'negative'
        else:
            return "undecidable"
        
    def _get_pick_time(self, ser, utc1): # get the utc time in first line1
        year, month, day = self._get_y_m_d(utc1)
        hour, minute, second = int(ser.hour), int(ser.minute), ser.second
        if hour >= 24:
            hour = hour - 24
            year, month, day = self._get_y_m_d(utc1 + 3600*24)
        utc = obspy.UTCDateTime(year=year, month=month, day=day, hour=hour, 
                                minute=minute)
        utc += second
        return utc
    
    def _get_y_m_d(self, utc):
        return int(utc.year), int(utc.month), int(utc.day)
        
    def _make_waveform_id(self, net, sta, loc, cha):
        widi = {}
        widi['network_code'] = net
        widi['station_code'] = sta
        widi['location_code'] = loc
        widi['channel_code'] = cha
        return obspy.core.event.WaveformStreamID(**widi)
        
    ### Get magnitudes
    def _get_magnitudes(self, sdf):
        
        df1 = sdf2df(sdf, '1')

        magkey = seisobs.specs.mag_key
        mags = []
        for num, row in df1.iterrows(): # iter through 1 lines
            # first magnitude
            mtype = magkey.get(row.magtype.upper(), 'M')
            m1 = self._create_magnitude(row.magnitude, mtype, row.magagency)
            self._append_mag_if_not_default(mags, m1)
            # second magnitude
            mtype = magkey.get(row.mag2type.upper(), 'M')
            m2 = self._create_magnitude(row.magnitude2, mtype, row.mag2agency)
            self._append_mag_if_not_default(mags, m2)         
            # third magnitude
            mtype = magkey.get(row.mag3type.upper(), 'M')
            m3 = self._create_magnitude(row.magnitude3, mtype, row.mag3agency)
            self._append_mag_if_not_default(mags, m3)           
        return mags 
    
    def _create_magnitude(self, mag, mag_type, mag_agency):
        madi = {}
        madi['mag'] = mag
        madi['magnitude_type'] = mag_type
        madi['creation_info'] = self._creation_info_generic(mag_agency)
        return obspy.core.event.Magnitude(**madi)
        
    def _append_mag_if_not_default(self, mags, mag):
        """
        decide if mag is defualt (null) magnitude or not. Append to mags
        if it is a valid mag
        """
        con1 =  mag.mag == 0.0
        con2 = mag.creation_info.agency_id is None
        con3 = mag.magnitude_type.upper() == 'M'
        if not (con1 and con2 and con3):
            mags.append(mag)

    def _creation_info_generic(self, agency=None, author=None, time=None):
        crdi = {}
        if agency:
            crdi['agency_id'] = agency
        if author:
            crdi['author'] = author
        if time:
            crdi['creation_time'] = time
        return obspy.core.event.CreationInfo(**crdi)
    
    def _get_comments_with_str(self, sdf, cstr):
        """
        Parse the comment lines and return those that have cstr
        """
        sdf3 = sdf[sdf.linetype=='3']
        scon = [cstr in x.series.comment for _, x in sdf3.iterrows()]
        return sdf3[scon]
    
    def _get_sfil_from_dir(self, sdir): # parse a sdirectory and yield the s files
        for root, dirs, files in os.walk(sdir, topdown=False):
            normpath = os.path.normpath(root)
            for fil in files:
                if not fil[-1] == '~' and not '.out' in fil:
                    yield os.path.join(normpath, fil)
    
    def _validate_sdf(self, sdf, sfile):
        """
        Function to validate the seisan dataframes
        """
        if len(sdf) < 1:
            msg = 'No valid seisan s lines or s-files (nordic) found'
            raise ValueError(msg)
        if not '1' in sdf.linetype.values:
            msg = 'sfile %s has no valid header line (linetype 1)'
            raise ValueError(msg)
        if not sdf.iloc[0].linetype == '1':
            msg = 'sfile %s does not begin with a lintype 1 entry' % sfile
            raise ValueError(msg)
    
    def gen_resource_id(self, sdf, id_type):
        """
        Function to generate a resource ID
        Params
        ------
        sdf : pd.DataFrame
            The pandas dataframe with 
        id_type : str
            The type of id to generate (prefix). Any string is allowed
        """
        resource_id = obspy.core.event.ResourceIdentifier(prefix=id_type)
        return resource_id
        
    def _get_utc(self, row): # take a one line row and return utc object
        ye = int(row.year)
        mo = int(row.month)
        da = int(row.day)
        ho = int(row.hour)
        mi = int(row.minute)
        sec = row.second
        utc = obspy.UTCDateTime(year=ye, month=mo, day=da, hour=ho, minute=mi)
        utc += sec
        return utc
    
    def _get_utc_from_I(self, seri):
        utc = obspy.core.UTCDateTime(seri.ID)
        return utc
        
    
    def warn(self, msg):
        """
        call self.warn for given message if verbose, else swallow
        """
        if self.verbose:
            warnings.warn(msg)

###### Sline class

class Sline(object):
    """
    object for storing sline info.
    """
    def __init__(self, sline=None, validate=True, seiob=None):
        self.slinetype = None
        self.sseries = None
        self.seiob = seiob
        if not (isinstance(sline, (text, str)) or sline is None):
            msg = 'sline must be a string or None'
            raise ValueError(msg)
        if sline:
            self.read_line(sline, validate)
        
    def read_line(self, sline, validate):
        """
        Function to read a line from an sfile (nordic)
        Parameters
        ----------
        sline : str
            A sfile line read in as a string
        validate : bool
            If True run the line-type's validation method which are found in 
            the specs module
        """
        sline = sline.rstrip(os.linesep)
        ltype = self._classify_line(sline)
        self.slinetype = ltype
        self.sline = sline
        if ltype == '4':
            try: # try loading and validating 
                self.sseries = self._load_sline(sline, ltype)
                seisobs.specs.specs[ltype].validate(self.sseries)
                
            except ValueError: #if this is really ment to be line 1
                msg = (('%s was assigned to linetype 4 but raised error, '
                        'trying linetype 1') % sline)
                if self.seiob is None:
                    warnings.warn(msg)
                else:
                    self.seiob.warn(msg)
                ltype = '1'
                self.sseries = self._load_sline(sline, ltype)
            self.sseries.linetype = ltype # set linetyp in series
        else:
            self.sseries = self._load_sline(sline, ltype)
            
                
        if validate:
            seisobs.specs.specs[ltype].validate(self.sseries)

    def _load_sline(self, sline, ltype):
        try:
            spec = seisobs.specs.specs[ltype]
        except KeyError:
            msg = '%s is not a supported line type of line %s' % (ltype, sline)
            raise KeyError(msg)
        sseries = pd.Series(index=spec.colname)
        for sp, na, fo in spec:
            str_val = sline[sp[0]:sp[1]]
            sc = seisobs.specs.get_string_converter(fo)
            sseries[na] = sc(str_val)            
        return sseries
            

    def _classify_line(self, sline):
        """
        function to classify the line from an s file. 
        """
        if len(sline) != 80:
            msg = 'the following line did not have 80 characters % s' % sline
            raise ValueError(msg)

        elif sline[79] == ' ':
            return '4'
        elif len(sline.strip()) < 1:
            return '0'
        else:
            return sline[79]
            
    def load_sfile_stream(self, arg):
        """
        Function to load the seisan file linked to an s-file into an obspy 
        stream
        
        arg : str, df, or Sline instance
            arg can be either a path to an s-file, a dataframe created with 
            the load_sfile_into_df function
        
        Returns
        --------
        An obspy Stream object
        """
        if isinstance(arg, text):
            df = self.load_sfile_into_df(arg)
        if isinstance(arg, pd.DataFrame):
            df = arg
        df6 = sdf2df(df, '6', self)
        if len(df6) != 1:
            msg = 'Exactly one line 6 is required, more or less were found'
            raise ValueError(msg)
        ser = df6.iloc[0].series
        path = ser.comment[:-1].rsplit()
        
        st = obspy.read(path)
        return st
        
    def __bool__(self):
         return (self.slinetype is not None) and (self.sseries is not None)
    
    def __str__(self):
        return self.sline
    
    def __repr__(self):
        return self.sseries.__repr__()

#### misc functions

def sdf2df(sdf, linetype, seisob=None):
    """
    Take the seisan data frame, which has two columns: linetype and series, 
    and collapse into a single dataframe given one linetype
    Parameters
    ---------
    sdf : pd.DataFrame
        The sdf as used in Seisob.seis2ob
    linetype : str
        The linetype to use in collapsing into single dataframe
    seisob : None or instance of Seisob
        Used for caching results to avoid redundant calculations
    
    Returns
    -------
    A dataframe with the columns being the indicies of linetype selected
    """
    if isinstance(seisob, Seisob):
        if linetype in seisob.df_cache:
            return seisob.df_cache[linetype]
        else:
            df = _sdf2df_helper(sdf, linetype)
            seisob.df_cache[linetype] = df
            return df
    else:
        return _sdf2df_helper(sdf, linetype)

def _sdf2df_helper(sdf, linetype):    
    sdflt = sdf[sdf.linetype == linetype]
    cols = seisobs.specs.specs[linetype].colname
    df = pd.DataFrame(columns=cols)
    for ind, row in sdflt.iterrows():
        df.loc[len(df)] = row.series
    return df
    
## Assign_wfid_methods, four functions for getting nslc codes

def get_nslc_from_comment(ser4=None, scnldf=None, **kwargs):
    con1 = scnldf.station == ser4.station
    con2 = scnldf.channel.str.contains(ser4.component)
    tdf = scnldf[con1 & con2]
    if len(tdf) < 1:
        msg = (('No matching scnl found in comments for station '
                ' %s component %s') % (ser4.station, ser4.component))
        raise ValueError(msg)
    if len(tdf) > 1:
        msg = 'More than one matching scnl found, using first'
        warnings.warn(msg)
    ser = tdf.iloc[0]
    return ser.network, ser.station, ser.location, ser.channel

def get_nslc_from_inventory(ser4=None, nslcdf=None, seiob=None, **kwargs):
    con1 = nslcdf.station==ser4.station
    con2 = nslcdf.station.str.contains(ser4.station)
    tdf = nslcdf[con1 & con2]
    if len(tdf) < 1:
        msg = 'No matching scnl found'
        raise ValueError(msg)
    if len(tdf) > 1:
        msg = 'More than one matching scnl found, using first'
        if seiob is None:
            warnings.warn(msg)
        else:
            seiob.warn(msg)
    ser = tdf.iloc[0]     
    return ser.network, ser.station, ser.location, ser.channel

def get_nscl_from_waveform(ser4=None, st=None, **kwargs):
    st1 = st.select(station=ser4.station, component=ser4.component)
    if len(st1) < 1:
        msg = (('No channel found in stream that meets the  '
                'requirements of %s' % ser4))
        raise ValueError(msg)
    if len(st1) > 1:
        msg = (('More than one channel meet requirements in stream' 
                '%s assuming first channel is correct') % st)
        warnings.warn(msg)
    tr = st[0]
    net, sta = tr.stats.network, tr.stats.station
    loc, cha = tr.stats.location, tr.stats.channel
    return net, sta, loc, cha

def get_nscl_from_thin_air(ser4=None, network='', channel_prefix='', **kwargs):
    net = network
    sta = ser4.station
    cha = channel_prefix + ser4.component
    loc = ' '
    return net, sta, loc, cha



        