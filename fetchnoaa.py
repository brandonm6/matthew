import os

from urllib.parse import urlencode
from urllib.request import urlopen
import io

import numpy as np


def fetch_noaa_tide_data(station, begin_date, end_date, time_zone='GMT',
                         datum='STND', units='metric', cache_dir=None,
                         verbose=True):
    """Fetch water levels and tide predictions at given NOAA tide station.

    The data is returned in 6 minute intervals between the specified begin and
    end dates/times.  A complete specification of the NOAA CO-OPS API for Data
    Retrieval used to fetch the data can be found at:

        https://tidesandcurrents.noaa.gov/api/

    By default, retrieved data is cached in the geoclaw scratch directory
    located at:

        $CLAW/geoclaw/scratch

    :Required Arguments:
    - station (string): 7 character station ID
    - begin_date (datetime): start of date/time range of retrieval
    - end_date (datetime): end of date/time range of retrieval

    :Optional Arguments:
    - time_zone (string): see NOAA API documentation for possible values
    - datum (string): see NOAA API documentation for possible values
    - units (string): see NOAA API documentation for possible values
    - cache_dir (string): alternative directory to use for caching data
    - verbose (bool): whether to output informational messages

    :Returns:
    - date_time (numpy.ndarray): times corresponding to retrieved data
    - water_level (numpy.ndarray): preliminary or verified water levels
    - prediction (numpy.ndarray): tide predictions
    """

    noaa_api_url = 'https://tidesandcurrents.noaa.gov/api/datagetter'

    # use geoclaw scratch directory for caching by default
    if cache_dir is None:
        if 'CLAW' not in os.environ:
            raise ValueError('CLAW environment variable not set')
        claw_dir = os.environ['CLAW']
        cache_dir = os.path.join(claw_dir, 'geoclaw', 'scratch')

    def fetch(product, expected_header, col_idx, col_types):
        noaa_params = get_noaa_params(product)
        cache_path = get_cache_path(product)

        # use cached data if available
        if os.path.exists(cache_path):
            if verbose:
                print('Using cached {} data for station {}'.format(
                    product, station))
            return parse(cache_path, col_idx, col_types, header=True)

        # otherwise, retrieve data from NOAA and cache it
        if verbose:
            print('Fetching {} data from NOAA for station {}'.format(
                product, station))
        full_url = '{}?{}'.format(noaa_api_url, urlencode(noaa_params))
        with urlopen(full_url) as response:
            text = response.read().decode('utf-8')
            with io.StringIO(text) as data:
                # ensure that received header is correct
                header = (data.readline()).strip()
            if header != expected_header or 'Error' in text:
                # response contains error message
                raise ValueError(text)
            # if there were no errors, then cache response
            save_to_cache(cache_path, text)
            return parse(data, col_idx, col_types, header=False)

    def get_noaa_params(product):
        noaa_date_fmt = '%Y%m%d %H:%M'
        noaa_params = {
            'product': product,
            'application': 'NOS.COOPS.TAC.WL',
            'format': 'csv',
            'station': station,
            'begin_date': begin_date.strftime(noaa_date_fmt),
            'end_date': end_date.strftime(noaa_date_fmt),
            'time_zone': time_zone,
            'datum': datum,
            'units': units
        }
        return noaa_params

    def get_cache_path(product):
        cache_date_fmt = '%Y%m%d%H%M'
        dates = '{}_{}'.format(begin_date.strftime(cache_date_fmt),
                               end_date.strftime(cache_date_fmt))
        filename = '{}_{}_{}'.format(time_zone, datum, units)
        abs_cache_dir = os.path.abspath(cache_dir)
        return os.path.join(abs_cache_dir, product, station, dates, filename)

    def save_to_cache(cache_path, data):
        # make parent directories if they do not exist
        parent_dir = os.path.dirname(cache_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        # write data to cache file
        with open(cache_path, 'w') as cache_file:
            cache_file.write(data)

    def parse(data, col_idx, col_types, header):
        # read data into structured array, skipping header row if present
        a = np.genfromtxt(data, usecols=col_idx, dtype=col_types,
                          skip_header=int(header), delimiter=',',
                          missing_values='')

        # return tuple of columns
        return tuple(a[col] for col in a.dtype.names)

    # only need first two columns of data; first column contains date/time,
    # and second column contains corresponding value
    col_idx = (0, 1)
    col_types = 'datetime64[m], float'

    # fetch water levels and tide predictions

    date_time, water_level = fetch(
        'water_level', 'Date Time, Water Level, Sigma, O or I (for verified), F, R, L, Quality',
        col_idx, col_types)

    date_time2, prediction = fetch('predictions', 'Date Time, Prediction',
                                   col_idx, col_types)

    # ensure that date/time ranges are the same
    if not np.array_equal(date_time, date_time2):
        raise ValueError('Received data for different times')

    return date_time, water_level, prediction


def get_actual_water_levels(station_id, begin_date, end_date, landfall_time):
    # Fetch water levels and tide predictions for given station
    date_time, water_level, tide = fetch_noaa_tide_data(station_id, begin_date, end_date, datum='NAVD')
    # Subtract tide predictions from measured water levels
    water_level -= tide
    # Calculate times relative to landfall
    seconds_rel_landfall = (date_time - landfall_time) / np.timedelta64(1, 's')

    return seconds_rel_landfall, water_level
