"""
A set of functions for dealing with multiple inversion runs together,
such as L-curve analysis
"""

import glob, json
from . import l_curve_plots


def read_param_from_list_of_config_files(filelist, paramname):
    """
    Read list of parameter value from a list of config files
    Ex: if you want to extract a series of smoothing values from sequential experiments
    """
    array_of_param_values = [];
    for file in filelist:
        config_file = open(file, 'r');
        tempdict = json.load(config_file)
        array_of_param_values.append(tempdict[paramname]);
    return array_of_param_values;


def read_fault_param_from_list_of_config_files(filelist, fault_name, param_name):
    """
    Read list of fault-specific parameter value from a list of config files
    Ex: if you want to extract a series of fault minimum slip rates
    """
    array_of_param_values = [];
    for file in filelist:
        config_file = open(file, 'r');
        tempdict = json.load(config_file)
        faults = tempdict["faults"];
        array_of_param_values.append(faults[fault_name][param_name]);
    return array_of_param_values;


def read_misfits_from_list_of_files(filelist, paramname):
    """
    Read list of parameter value from a list of human-readable results files
    Ex: if you want to extract a series of smoothing values from sequential experiments
    """
    misfit_values = [];
    for ifile in filelist:
        with open(ifile, 'r') as fp:
            for line in fp:
                # if 'Average misfit' in line:
                if paramname in line:   # Have found that misfit should consider sigmas
                    misfit = float(line.split()[-2]);  # misfit metric somehow
                    misfit_values.append(misfit);
    return misfit_values;


def read_values_from_list_of_files(filelist, paramname):
    """
    Read list of parameter value from a list of human-readable results files
    Ex: if you want to extract a series of smoothing values from sequential experiments
    """
    values = [];
    for ifile in filelist:
        with open(ifile, 'r') as fp:
            for line in fp:
                if paramname in line:
                    value = float(line.split()[1]);  # slip rate value
                    values.append(value);
    return values;


def glob_and_drive_1d_lcurve(target_dir='.', name_of_printed_config="configs_used.txt", paramname='smoothing',
                             name_of_results_file="model_results_human.txt", misfitname="RMS",
                             outname="smoothing_curve.png", xlabel="Smoothing", corner_point=None):
    """
    Get every smoothing parameter in a directory where smoothing experiment has been run multiple times.

    :param target_dir: directory name
    :param name_of_printed_config: file name
    :param paramname: string, found within config_file
    :param name_of_results_file: file name
    :param misfitname: string, found within results_file
    :param outname: string
    :param xlabel: string
    :param corner_point: float, optional x-location where an annotation will be drawn
    """
    config_files = glob.glob(target_dir+"/**/"+name_of_printed_config);
    results_files = glob.glob(target_dir + "/**/" + name_of_results_file);
    smoothings = read_param_from_list_of_config_files(config_files, paramname);
    misfits = read_misfits_from_list_of_files(results_files, misfitname);
    l_curve_plots.plot_1d_curve(smoothings, misfits, xlabel, outname, corner_point);
    return;
