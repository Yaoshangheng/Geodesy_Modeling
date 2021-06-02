# A series of functions for io of leveling data
# including CEC Salton Trough Leveling Data

import collections
import datetime as dt
import numpy as np
import xlrd
import pandas

LevStation = collections.namedtuple("LevStation", ["name", "lat", "lon", "dtarray", "leveling", "reflon", "reflat"]);
# LevStation: list-of-objects format, one object for each station. Units of meters.


def inputs_brawley_leveling(data_filename, errors_filename):
    """Read leveling from CEC Salton Trough North Brawley leveling data"""
    print("Reading in %s" % data_filename);
    df = pandas.read_excel(data_filename, engine='openpyxl');

    # Fix typos
    [rownum, colnum, _old_values, new_values] = read_errors(errors_filename);
    df = implement_changes_dataframe(df, rownum, colnum, new_values);

    # Reading name information
    column_names = df.columns[1:-1].tolist();
    names = df['BENCHMARK'].values.tolist();
    dtarray = get_datetimes(column_names);

    # Reading lat/lon information
    lonlat_sheet = pandas.read_excel(data_filename, engine='openpyxl', sheet_name=2);
    ll_names = lonlat_sheet['Benchmark'].values.tolist();
    longitudes = [float(x) for x in lonlat_sheet['Longitude'].values.tolist()];
    latitudes = [float(x) for x in lonlat_sheet['Latitude'].values.tolist()];
    names, lons, lats = match_lon_lat(names, latitudes, longitudes, ll_names);

    LevStationList = [];
    for x in range(1, 83):
        single_leveling_array = df.loc[x][1:-1].tolist();
        single_leveling_array = clean_single_ts(single_leveling_array);
        new_object = LevStation(name=names[x-1], lon=lons[x-1], lat=lats[x-1], dtarray=dtarray,
                                leveling=single_leveling_array, reflon=lons[0], reflat=lats[0]);
        LevStationList.append(new_object);
    return LevStationList;


def read_errors(filename):
    print("Reading documented errors in %s " % filename)
    rownum, colnum = [], [];
    old_values, new_values = [], [];
    ifile = open(filename, 'r');
    for line in ifile:
        temp = line.split("::");
        if temp[0] == "#":
            continue;
        rownum.append(int(temp[0]));
        colnum.append(int(temp[1]));
        old_values.append(temp[2]);
        new_values.append(temp[3]);
    ifile.close();
    return [rownum, colnum, old_values, new_values];


def implement_changes_dataframe(df, rownum, colnum, new_values):
    print("Implementing changes to data:");
    for i in range(len(rownum)):
        col_names = df.columns[0:-1].tolist();
        print("Finding error in column %s" % col_names[colnum[i]-1])  # get the right column
        old_value = df.iloc[rownum[i]-2, colnum[i]-1];
        df.iloc[rownum[i]-2, colnum[i]-1] = new_values[i];  # assignment
        print("   Carefully replacing %s with %s" % (old_value, new_values[i]) );
    return df;


def get_datetimes(timestrings):
    dtarray = [];
    for i in range(len(timestrings)):
        # Normal dates
        if " 88 " in timestrings[i]:
            temp = timestrings[i].split(" 88 ");
            temp2 = temp[1].split();
            mmm = temp2[0];
            if mmm == ')CT':
                mmm = 'OCT';   # fixing a typo
            year = temp2[1];
            dtarray.append(dt.datetime.strptime(year + "-" + mmm + "-01",
                                                "%Y-%b-%d"));  # issue here, but not too bad.
        else:  # For the special cases
            if "NOLTE 2008" in timestrings[i]:
                dtarray.append(dt.datetime.strptime("2008-Nov-01", "%Y-%b-%d"));
    return dtarray;


def match_lon_lat(names, lats, lons, ll_names):
    """Pair up the latlon info with the timeseries info"""
    matched_lons, matched_lats = [], [];
    for i in range(len(names)):
        find_name = names[i];
        if names[i] == "Y-1225 Datum":
            find_name = "Y 1225";
        idx = ll_names.index(find_name);
        matched_lats.append(lats[idx]);
        matched_lons.append(lons[idx]);
    return [names, matched_lons, matched_lats];


def clean_single_ts(array):
    newarray = [];
    for i in range(len(array)):
        if str(array[i]) == "-" or str(array[i]) == "DESTROYED" or str(array[i]) == "DAMAGED" or str(
                array[i]) == "NOT" or str(array[i]) == "FOUND":
            newarray.append(np.nan);
        else:
            newarray.append(float(array[i]));
    return newarray;


# LEVELING COMPUTE FUNCITON (REFERENCE TO DATUM)
def compute_rel_to_datum_nov_2009(data):
    """Skips the 2008 measurement. Returns an object that is 83x10"""
    RefLevStations = [];
    for station in data:

        # Automatically find the first day that matters.  Either after 2008 or has data.
        idx = 0;
        for j in range(len(station.dtarray)):
            if ~np.isnan(station.leveling[j]) and station.dtarray[j] > dt.datetime.strptime("2009-01-01", "%Y-%m-%d"):
                idx = j;  # this is the first date after 2009 that has data
                break;

        # Accounting for a change in Datum height in 2014
        idx_early = 6;  # the placement of 2014 before adjustment on the spreadsheet
        idx_late = 7;  # the placement of 2014 after adjustment on the spreadsheet
        step = station.leveling[idx_early] - station.leveling[idx_late];

        referenced_dates, referenced_data = [], [];
        for j in range(1, len(station.dtarray)):  # skipping 2008 anyway.
            if j == 6:
                continue;  # passing over the 2014 measurement before re-referencing.
            if station.dtarray[j] > dt.datetime.strptime("2014-01-01", "%Y-%m-%d"):
                referenced_dates.append(station.dtarray[j]);
                referenced_data.append(station.leveling[j] - station.leveling[idx] + step);
            else:
                referenced_dates.append(station.dtarray[j]);
                referenced_data.append(station.leveling[j] - station.leveling[idx]);


        referenced_object = LevStation(name=station.name, lon=station.lon, lat=station.lat, dtarray=referenced_dates,
                                       leveling=referenced_data, reflon=station.reflon, reflat=station.reflat);
        RefLevStations.append(referenced_object);
    return RefLevStations;


# HEBER DATA SPREADSHEET
def inputs_leveling_heber(infile):
    """CEC HEBER LEVELING SPREADSHEET INTO LIST OF LEVELING OBJECTS.
    WILL HAVE TO FIX THIS BECAUSE XLRD DOESN'T SUPPORT XLSX ANYMORE"""
    station_list = [];
    print("Reading in %s" % infile);
    wb = xlrd.open_workbook(infile);

    # Get locations of benchmarks and reference benchmark, with the reference in the first line.
    sheet = wb.sheet_by_index(1);
    numcols = sheet.ncols;
    numrows = sheet.nrows;
    locdata = [[sheet.cell_value(r, c) for c in range(numcols)] for r in range(numrows)];
    locnames = []; all_lons = []; all_lats = [];
    for i in range(1, 185):
        if locdata[i][1] != "":
            latstring = str(locdata[i][1]);
            latstring = latstring.replace('..', '.');
            lonstring = str(locdata[i][2]);
            lonstring = lonstring.replace('..', '.');
            locnames.append(locdata[i][0]);
            all_lats.append(float(latstring));
            all_lons.append(float(lonstring));
    reflat = all_lats[0];
    reflon = all_lons[0];

    # Get leveling data from the spreadsheet
    sheet = wb.sheet_by_index(0);
    numcols = sheet.ncols;
    numrows = sheet.nrows;
    data = [[sheet.cell_value(r, c) for c in range(numcols)] for r in range(numrows)];

    # Get dates for all leveling array
    dtarray = [];
    for i in range(32, 57):  # take the first column of the third sheet
        dtarray.append(dt.datetime.strptime(data[i][0], "%b %Y"));

    # Extract each station's leveling data
    for colnum in range(5, 163):  # for each station's leveling data
        station_name = data[31][colnum];  # the string station name
        levarray = [];
        for i in range(32, 57):
            if data[i][colnum] in ["DESTROYED", "", "NOT FOUND", "?", "UNACCESSABLE ", "LOST"]:
                levarray.append(np.nan);
            else:
                levarray.append(float(data[i][colnum]));
        # print(station_name, len(levarray), len(dtarray));
        station_lon_idx = locnames.index(station_name);
        new_station = LevStation(name=station_name, lat=all_lats[station_lon_idx], lon=all_lons[station_lon_idx],
                                 dtarray=dtarray, leveling=levarray, reflon=reflon, reflat=reflat);
        station_list.append(new_station);
    print("Returning %d leveling stations " % len(station_list));
    return station_list;
