# WORK ON REDUCING NUMBER OF FOR-LOOPS (INCREASING EFFICIENCY)

import numpy as np
import pandas as pd

pd.options.mode.chained_assignment = None  # default='warn'


def kml2slu(file):
    """
    Converts Polygons drawn in Google Earth to slu used by GeoClaw flag_regions - slus are outputted to a .txt file
    named slu_ouputs and are also returned in a dictionary where key is the name of the Polygon and value is the slu
    in numpy array format

    file: .kml file downloaded from Google Earth - there can't be any three points on the polygon with same the latitude
    """

    class Segment:
        # Stores info needed for each line segment making up the polygon
        def __init__(self, x0, x1, y0, y1):
            self.x = x0
            self.y = y0
            self.ylower = np.min([y0, y1])
            self.yupper = np.max([y0, y1])
            self.slope = (y1 - y0) / (x1 - x0)

    polygons = {}

    placemark = False
    name = None
    polygon = False
    grab_next = False

    with open(file, "r") as kml_file:
        for num, line in enumerate(kml_file, 1):
            if "<Placemark>" in line:
                placemark = True

            elif placemark:
                if "<name>" in line:
                    name = line[line.find(">") + 1:line.find("</")]
                elif "<Polygon>" in line:
                    polygon = True
                elif ("<coordinates>" in line) and polygon:
                    grab_next = True
                elif grab_next:
                    # Grabs coordinates of points and puts them in dataframe with [lat, lon]
                    s = pd.Series(np.array(line.strip().split(" "))).str.split(",")
                    df = pd.concat([s.str.get(0).astype(float), s.str.get(1).astype(float)], axis=1)
                    df.columns = ["lon", "lat"]

                    # Identify polygon segments
                    segments = [
                        Segment(df["lon"].iloc[i], df["lon"].iloc[i + 1], df["lat"].iloc[i], df["lat"].iloc[i + 1])
                        for i in df.index.to_list() if i != len(df) - 1]

                    # Get longitudes for each latitude
                    df["lon 0"] = None
                    df["lon 1"] = None
                    for i in df.index.to_list():
                        lat = df["lat"].iloc[i]
                        lon_orig = df["lon"].iloc[i]
                        for seg in segments:
                            if seg.ylower <= lat <= seg.yupper:
                                lon = ((lat - seg.y) / seg.slope) + seg.x
                                if lon != lon_orig:
                                    if lon > lon_orig:
                                        df["lon 1"].iloc[i] = lon
                                        df["lon 0"].iloc[i] = lon_orig
                                    else:
                                        df["lon 1"].iloc[i] = lon_orig
                                        df["lon 0"].iloc[i] = lon

                        # For top and bottom verticies
                        if df["lon 0"].iloc[i] is None and df["lon 1"].iloc[i] is None:
                            df["lon 0"].iloc[i] = lon_orig
                            df["lon 1"].iloc[i] = lon_orig

                    df = df.drop_duplicates(subset=['lat']).reset_index(drop=True)
                    polygons[name] = df[["lat", "lon 0", "lon 1"]].sort_values(by=['lat']).to_numpy()

                    polygon = False
                    grab_next = False
                    placemark = False

    with open("slu_ouputs.txt", "w") as slu_file:
        for polygon in polygons:
            slu_file.writelines([polygon, ":\n", str(polygons.get(polygon)), "\n\n"])

    return polygons
