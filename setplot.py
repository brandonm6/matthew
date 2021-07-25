from __future__ import absolute_import
from __future__ import print_function

import os

import numpy as np
import matplotlib.pyplot as plt
import datetime

import clawpack.visclaw.gaugetools as gaugetools
import clawpack.clawutil.data as clawutil
import clawpack.geoclaw.data as geodata

import clawpack.geoclaw.surge.plot as surgeplot

import requests

try:
    from setplotfg import setplotfg
except ModuleNotFoundError:
    setplotfg = None


# Time Conversions
def days2seconds(days):
    return days * 60.0 ** 2 * 24.0


def setplot(plotdata=None):
    if plotdata is None:
        from clawpack.visclaw.data import ClawPlotData
        plotdata = ClawPlotData()

    # clear any old figures,axes,items data
    plotdata.clearfigures()
    plotdata.format = 'ascii'

    # Load data from output
    clawdata = clawutil.ClawInputData(2)
    clawdata.read(os.path.join(plotdata.outdir, 'claw.data'))
    physics = geodata.GeoClawData()
    physics.read(os.path.join(plotdata.outdir, 'geoclaw.data'))
    surge_data = geodata.SurgeData()
    surge_data.read(os.path.join(plotdata.outdir, 'surge.data'))
    friction_data = geodata.FrictionData()
    friction_data.read(os.path.join(plotdata.outdir, 'friction.data'))

    # Load storm track
    track = surgeplot.track_data(os.path.join(plotdata.outdir, 'fort.track'))

    # Set afteraxes function
    def surge_afteraxes(current_data):
        surgeplot.surge_afteraxes(current_data, track, plot_direction=False,
                                  kwargs={"markersize": 4})

    # Color limits
    surface_limits = [-5.0, 5.0]
    speed_limits = [0.0, 3.0]
    wind_limits = [0, 64]
    pressure_limits = [935, 1013]
    friction_bounds = [0.01, 0.04]
    color_limits = [0, 50]

    def friction_afteraxes(current_data):
        plt.title(r"Manning's $n$ Coefficient")

    # Standard set-up for plots
    def standard_setup(title, xlimits, ylimits, axes_type):
        plotaxes.title = title
        plotaxes.xlimits = xlimits
        plotaxes.ylimits = ylimits
        plotaxes.afteraxes = axes_type
        plotaxes.scaled = True

    # ==========================================================================
    #   Plot specifications
    # ==========================================================================
    regions = {"Full Domain": {"xlimits": (clawdata.lower[0],
                                           clawdata.upper[0]),
                               "ylimits": (clawdata.lower[1],
                                           clawdata.upper[1])},
               "Carolinas": {"xlimits": (-80.5, -77.0),
                             "ylimits": (31.5, 35)}}

    for (name, region_dict) in regions.items():
        # Surface Figure
        plotfigure = plotdata.new_plotfigure(name="Surface - %s" % name)
        plotaxes = plotfigure.new_plotaxes()
        standard_setup("Surface", region_dict["xlimits"], region_dict["ylimits"], surge_afteraxes)

        surgeplot.add_surface_elevation(plotaxes, bounds=surface_limits)
        surgeplot.add_land(plotaxes)
        plotaxes.plotitem_dict['surface'].amr_patchedges_show = [0] * 10
        plotaxes.plotitem_dict['land'].amr_patchedges_show = [0] * 10

        # Speed Figure
        plotfigure = plotdata.new_plotfigure(name="Currents - %s" % name)
        plotaxes = plotfigure.new_plotaxes()
        standard_setup("Currents", region_dict["xlimits"], region_dict["ylimits"], surge_afteraxes)

        surgeplot.add_speed(plotaxes, bounds=speed_limits)
        surgeplot.add_land(plotaxes, bounds=color_limits)
        plotaxes.plotitem_dict['speed'].amr_patchedges_show = [0] * 10
        plotaxes.plotitem_dict['land'].amr_patchedges_show = [0] * 10
    #
    # Friction field
    #
    plotfigure = plotdata.new_plotfigure(name='Friction')
    plotfigure.show = friction_data.variable_friction and True
    plotaxes = plotfigure.new_plotaxes()
    standard_setup(None, regions['Full Domain']['xlimits'], regions['Full Domain']['ylimits'], friction_afteraxes)

    surgeplot.add_friction(plotaxes, bounds=friction_bounds)
    plotaxes.plotitem_dict['friction'].amr_patchedges_show = [0] * 10
    plotaxes.plotitem_dict['friction'].colorbar_label = "$n$"

    #
    #  Hurricane Forcing fields
    #
    # Pressure field
    plotfigure = plotdata.new_plotfigure(name='Pressure')
    plotfigure.show = surge_data.pressure_forcing and True
    plotaxes = plotfigure.new_plotaxes()
    standard_setup("Pressure Field", regions['Full Domain']['xlimits'], regions['Full Domain']['ylimits'],
                   surge_afteraxes)

    surgeplot.add_pressure(plotaxes, bounds=pressure_limits)
    surgeplot.add_land(plotaxes)

    # Wind field
    plotfigure = plotdata.new_plotfigure(name='Wind Speed')
    plotfigure.show = surge_data.wind_forcing and True
    plotaxes = plotfigure.new_plotaxes()
    standard_setup("Wind Field", regions['Full Domain']['xlimits'], regions['Full Domain']['ylimits'], surge_afteraxes)

    surgeplot.add_wind(plotaxes, bounds=wind_limits)
    surgeplot.add_land(plotaxes)

    # ========================================================================
    #  Figures for gauges
    # ========================================================================
    plotfigure = plotdata.new_plotfigure(name='Surface', figno=300,
                                         type='each_gauge')
    plotfigure.show = True
    plotfigure.clf_each_gauge = True

    stations = [('8720218', 'Mayport (Bar Pilots Dock), FL'),
                ('8720219', 'Dames Point, FL'),
                ('8670870', 'Fort Pulaski, GA'),
                ('8665530', 'Charleston, Cooper River Entrance, SC'),
                ('8662245', 'Oyster Landing (N Inlet Estuary), SC'),
                ('8658163', 'Wrightsville Beach, NC'),
                ('8658120', 'Wilmington, NC')]

    landfall_time = np.datetime64('2016-10-08T12:00')
    begin_date = datetime.datetime(2016, 10, 6, 12)
    end_date = datetime.datetime(2016, 10, 9, 12)

    def fetch_noaa_tide_data(station, begin_date, end_date, time_zone='GMT',
                             datum='STND', units='metric', cache_dir=None,
                             verbose=True):

        begin_date = begin_date.strftime('%Y%m%d %H:%M')
        end_date = end_date.strftime('%Y%m%d %H:%M')

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
            response = requests.get(noaa_api_url, noaa_params)
            text = response.text
            # ensure that received header is correct
            header = text.splitlines()[0].strip()
            if header != expected_header or not response:
                # response contains error message
                raise ValueError("text")
            # if there were no errors, then cache response
            save_to_cache(cache_path, text)

            return parse(cache_path, col_idx, col_types, header=True)

        def get_noaa_params(product):
            noaa_params = {
                'product': product,
                'application': 'NOS.COOPS.TAC.WL',
                'format': 'csv',
                'station': station,
                'begin_date': begin_date,
                'end_date': end_date,
                'time_zone': time_zone,
                'datum': datum,
                'units': units
            }
            return noaa_params

        def get_cache_path(product):
            dates = '{}_{}'.format(begin_date, end_date)
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

    def gauge_afteraxes(current_data):
        axes = plt.gca()

        surgeplot.plot_landfall_gauge(current_data.gaugesoln, axes)
        station_id, station_name = stations[current_data.gaugeno - 1]

        seconds_rel_landfall, actual_level = get_actual_water_levels(station_id, begin_date, end_date,
                                                                     landfall_time)
        axes.plot(seconds_rel_landfall, actual_level, 'g', label='Observed')

        # Fix up plot - in particular fix time labels
        axes.set_title(station_name + " - Station ID: " + station_id)
        axes.set_xlabel('Days relative to landfall')
        axes.set_ylabel('Surface (m)')
        axes.set_xlim([days2seconds(-2), days2seconds(1)])
        axes.set_ylim([-1, 3])
        axes.set_xticks([days2seconds(-2), days2seconds(-1), 0, days2seconds(1)])
        axes.set_xticklabels([r"$-2$", r"$-1$", r"$0$", r"$1$"])
        axes.grid(True)
        plt.legend(loc="upper left")

    # Set up for axes in this figure:
    plotaxes = plotfigure.new_plotaxes()
    plotaxes.afteraxes = gauge_afteraxes
    # Plot surface as blue curve:
    plotitem = plotaxes.new_plotitem(plot_type='1d_plot')
    plotitem.plot_var = 3
    plotitem.plotstyle = 'b-'

    #
    #  Gauge Location Plot
    #
    gauge_regions = {"Carolinas": {"xlimits": (-80.5, -77.0),
                                   "ylimits": (31.5, 35),
                                   "gaugenos": [4, 5, 6, 7]},
                     "All": {"xlimits": (-82.0, -77.0),
                             "ylimits": (30.0, 35.0),
                             "gaugenos": "all"},
                     "Mayport": {"xlimits": (-81.435, -81.39),
                                 "ylimits": (30.39, 30.41),
                                 "gaugenos": [1]},
                     "Dames Point": {"xlimits": (-81.57, -81.38),
                                     "ylimits": (30.37, 30.42),
                                     "gaugenos": [2]},
                     "Fort Pulaski": {"xlimits": (-80.91, -80.85),
                                      "ylimits": (32.03, 32.04),
                                      "gaugenos": [3]},
                     "Charleston, Cooper River Entrance": {"xlimits": (-79.93, -79.86),
                                                           "ylimits": (32.75, 32.79),
                                                           "gaugenos": [4]},
                     "Oyster Landing": {"xlimits": (-79.20, -79.18),
                                        "ylimits": (33.34, 33.36),
                                        "gaugenos": [5]},
                     "Wrightsville Beach": {"xlimits": (-77.7875, -77.7850),
                                            "ylimits": (34.2120, 34.2145),
                                            "gaugenos": [6]},
                     "Wilmington": {"xlimits": (-77.98, -77.93),
                                    "ylimits": (33.95, 34.25),
                                    "gaugenos": [7]}}

    '''
    if plotdata.parallel = False, multiply queue by frameno
    if plotdata.parallel = True, multiply queue by int((frameno/2) + 0.5)
    '''
    frameno = len([file for file in os.listdir(plotdata.outdir) if "fort.q" in file])
    queue = [key for key in gauge_regions.keys()] * int((frameno / 2) + 0.5)

    def which_gauges():
        # Returns gaugenos from current region_dict - used by gauge_location_afteraxes
        gaugenos = (gauge_regions[queue[0]])["gaugenos"]
        queue.pop(0)
        return gaugenos

    def gauge_location_afteraxes(current_data):
        plt.subplots_adjust(left=0.12, bottom=0.06, right=0.97, top=0.97)
        surge_afteraxes(current_data)
        gaugetools.plot_gauge_locations(current_data.plotdata, gaugenos=which_gauges(),
                                        format_string='ko', add_labels=True)

    for (name, region_dict) in gauge_regions.items():
        plotfigure = plotdata.new_plotfigure(name="Gauge Locations - %s" % name)
        plotaxes = plotfigure.new_plotaxes()
        standard_setup("Gauge Locations", region_dict["xlimits"], region_dict["ylimits"], gauge_location_afteraxes)

        surgeplot.add_surface_elevation(plotaxes, bounds=surface_limits)
        surgeplot.add_land(plotaxes)
        plotaxes.plotitem_dict['surface'].amr_patchedges_show = [0] * 10
        plotaxes.plotitem_dict['land'].amr_patchedges_show = [0] * 10

    # -----------------------------------------
    # Parameters used only when creating html and/or latex hardcopy
    # e.g., via pyclaw.plotters.frametools.printframes:

    plotdata.printfigs = True  # print figures
    plotdata.print_format = 'png'  # file format
    plotdata.print_framenos = 'all'  # list of frames to print
    plotdata.print_gaugenos = 'all'  # list of gauges to print
    plotdata.print_fignos = 'all'  # list of figures to print
    plotdata.html = True  # create html files of plots?
    plotdata.latex = True  # create latex file of plots?
    plotdata.latex_figsperline = 2  # layout of plots
    plotdata.latex_framesperline = 1  # layout of plots
    plotdata.latex_makepdf = False  # also run pdflatex?
    plotdata.parallel = True  # parallel plotting

    return plotdata
