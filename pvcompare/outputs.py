from pvcompare import check_inputs
import pvcompare.main as main
import pvcompare.constants as constants
import os
import pandas as pd
import shutil
import glob
import matplotlib.pyplot as plt
import logging


def loop(
    latitude,
    longitude,
    year,
    population,
    country,
    variable_name,
    variable_column,
    csv_file_variable,
    start,
    stop,
    step,
    scenario_name,
    mvs_input_directory=None,
    output_directory = None,
):
    """
    Starts multiple MVS simulations with a range of values for a specific parameter.

    After calculating the pvcompare time series with :py:func:`~.main.main`, :py:func:`~.main.apply_mvs` is
    executed in a loop. Before each loop a specific variable value is changed. The
    results, stored in two excel sheets are copied into `loop_output_directory`.

    Parameters
    ----------
    latitude: float
        latitude of the location
    longitude: foat
        longitude of the location
    year: int
        year
    population:int
        number of habitants
    country: str
        country of location
    variable_name: str
        name of the variable that is atapted in each loop
    variable_column: str
        name of the  variable column in the csv file
    csv_file_variable: str
        name of the csv file the variable is saved in
    start: int
        first value of the variable
    stop: int
        last value of the variable. notice that stop > start
    step: int
        step of increase
    scenario_name: str
        Name of the Scenario. The name should follow the scheme:
        "Scenario_A1", "Scenario_A2", "Scenario_B1" etc.
    output_directory: str
        Path to output directory.
        Default: constants.DEFAULT_OUTPUT_DIRECTORY
    mvs_input_directory: str or None
        if None then value will be taken from constants.py

    Returns
    -------

    """

    if mvs_input_directory == None:
        mvs_input_directory = constants.DEFAULT_MVS_INPUT_DIRECTORY
    if output_directory == None:
        output_folder = os.path.join(constants.DEFAULT_OUTPUT_DIRECTORY, scenario_name)
        loop_output_directory = os.path.join(output_folder, "loop_outputs_"+str(variable_name))
    else:
        loop_output_directory = os.path.join(output_directory, scenario_name, "loop_outputs_"+str(variable_name))

    if not os.path.isdir(output_folder):
        # create output folder
        os.mkdir(output_folder)

    if os.path.isdir(loop_output_directory):
        raise NameError(f"The loop output directory {loop_output_directory} "
                        f"already exists. Please "
                        f"delete the existing folder or rename {scenario_name}.")
    else:
            os.mkdir(loop_output_directory)

    # create output folder in loop_output_directories for "scalars" and "timeseries"
    os.mkdir(os.path.join(loop_output_directory, "scalars"))
    os.mkdir(os.path.join(loop_output_directory, "timeseries"))

    csv_filename = os.path.join(mvs_input_directory, "csv_elements", csv_file_variable)
    csv_file = pd.read_csv(csv_filename, index_col=0)

    main.main(
        latitude=latitude,
        longitude=longitude,
        year=year,
        population=population,
        country=country,
    )

    i = start
    while i <= stop:
        csv_file.loc[[variable_name], [variable_column]] = i
        # save csv
        csv_file.to_csv(csv_filename)

        mvs_output_directory = os.path.join(
            constants.DEFAULT_OUTPUT_DIRECTORY, scenario_name,
            "mvs_outputs_loop_" + str(variable_name)+"_"+str(i))

        main.apply_mvs(scenario_name=scenario_name, mvs_output_directory = mvs_output_directory)

        # copy excel sheets to loop_output_directory
        number_digits = len(str(stop)) - len(str(i))

        if number_digits == 0:
            j = str(i)
        elif number_digits == 1:
            j = "0" + str(i)
        elif number_digits == 2:
            j = "00" + str(i)
        elif number_digits == 3:
            j = "000" + str(i)
        elif number_digits == 4:
            j = "0000" + str(i)

        excel_file1 = "scalars.xlsx"
        new_excel_file1 = "scalars_" + str(j) + ".xlsx"
        src_dir = os.path.join(mvs_output_directory, excel_file1)
        dst_dir = os.path.join(loop_output_directory, "scalars", new_excel_file1)
        shutil.copy(src_dir, dst_dir)

        excel_file2 = "timeseries_all_busses.xlsx"
        new_excel_file2 = "timeseries_all_busses_" + str(j) + ".xlsx"
        src_dir = os.path.join(mvs_output_directory, excel_file2)
        dst_dir = os.path.join(loop_output_directory, "timeseries", new_excel_file2)
        shutil.copy(src_dir, dst_dir)

        i = i + step


def plot_all_flows(
    output_directory=None,
    timeseries_directory=None,
    timeseries_name="timeseries_all_busses.xlsx",
    month=None,
    calendar_week=None,
    weekday=None,
):

    """
    Plots all flows of the energy system for a given period of time.

    Parameters
    ----------
    month: int
        Number of month that should be plotted.
        Only fill in a number here, if you want to plot over one month.
        If None: will plot over week, weekday or the whole year. Default: None
    calendar_week: int
        the week (number in calender weeks) that should be plotted.
        Only fill in a number here, if you want to plot over one a week or a weekday.
        if None: will plot over one month or the whole year. Default: None
    weekday: int
        The day of the caldendar_week (from 0-6 with 0 : Monday and 6: Sunday.
        If None: the next greater period is plotted. Default: None
    output_directory: str or None
        Path to the directory in which the plot should be saved.
        Default: None.
        If None: `output_directory = constants.DEFAULT_MVS_OUTPUT_DIRECTORY`
    timeseries_directory: str or None
        Path to the timeseries directory.
        If None: `timeseries_directory = output_directory`.
        Default: None.
    timeseries_name: str or None
        Default: timeseries_all_busses.xlsx

    Returns
    -------
        None
        Saves figure into output_directory
    -------


    """
    # check if weekday is a valid day
    if weekday not in range(0, 6, 1):
        logging.error(
            "The weekday is not valid. Please choose a number "
            "between 0-6 with 0:Monaday and 6:Sunday."
        )
    # read timeseries
    if output_directory == None:
        output_directory = constants.DEFAULT_MVS_OUTPUT_DIRECTORY
    if timeseries_directory == None:
        timeseries_directory = output_directory
    df = pd.read_excel(
        os.path.join(timeseries_directory, timeseries_name),
        sheet_name="Electricity_bus",
        index_col=0,
    )
    # Converting the index as date
    df.index = pd.to_datetime(df.index)

    # define period for the plot
    if month is None:
        if calendar_week is None:
            period = "year"
            pass
            if weekday is not None:
                logging.error(
                    "If you want to create a plot over one weekday, please "
                    "define a caldendar_week as well. Otherwise set"
                    " weekday to 'None'."
                )
        else:
            if weekday is not None:
                df = df[df.index.week == calendar_week]
                df = df[df.index.weekday == weekday]
                period = "day_" + str(calendar_week) + "_" + str(weekday)
            else:
                df = df[df.index.week == calendar_week]
                period = "caldendar_week_" + str(calendar_week)
    else:
        if calendar_week is not None:
            if weekday is None:
                logging.warning(
                    "You inserted a month and a week. In this case the "
                    "plot will cover one caldendar_week. If you want to plot "
                    "over one month please set the calendar_week to 'None'"
                )
                df = df[df.index.week == calendar_week]
                period = "week_" + str(calendar_week)
            else:
                logging.warning(
                    "You inserted a month, a caldendar_week and a weekday. In this case the "
                    "plot will cover one weekday only. If you want to plot "
                    "over one month please set the caldendar_week and weekday to 'None'"
                )
                df = df[df.index.week == calendar_week]
                df = df[df.index.weekday == weekday]
                period = "day_" + str(calendar_week) + "_" + str(weekday)
        else:
            df = df[df.index.month == month]
            period = "month_" + str(month)

    # plot
    plt.title("All Flows", color="black")
    df.plot().legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.0)
    plt.xlabel("time")
    plt.ylabel("kW")

    # save plot into output directory
    plt.savefig(
        os.path.join(output_directory, f"plot_{timeseries_name[:-5]}_{period}.png"),
        bbox_inches="tight",
    )


def plot_kpi_loop(variable_name, kpi, scenario_name, output_directory=None, loop_output_directory = None):

    """
    Plots KPI's from the 'mvs_output/scalars_**.xlsx' files in `loop_outputs`
    for a loop over one variable.

    The 'energyProduction.csv' needs to be saved into 'output_directory'. If the
    loop output is created with :py:func:`~.automated_loop.loop`, the
    'energyProduction.csv' file is copied into the `output_directory` automatically.

    The plot is saved into the `loop_output_directory`.

    Parameters
    ----------
    variable_name: str
        Name of the variable that is changed each loop. Please do not enter
        white spaces within the string.
    kpi: list of str
        List of KPI's to be plotted.
        Possible entries:
            "costs total PV",
            "installed capacity PV",
            "Total renewable energy use",
            "Renewable share",
            "LCOE PV",
            "self consumption",
            "self sufficiency",
            "Degree of autonomy"
    scenario_name: str
        Name of the Scenario. The name should follow the scheme:
        "Scenario_A1", "Scenario_A2", "Scenario_B1" etc.
    output_directory: str
        Path to output directory.
        Default: constants.DEFAULT_OUTPUT_DIRECTORY
    loop_output_directory: str
        Path to loop output directory
        Default: os.path.join(output_directory, 'scenario_name', loop_outputs + str(variable_name))

    Returns
    -------
        None
        saves figure into `loop_output_directory`
    -------


    """

    if output_directory == None:
        output_folder = os.path.join(constants.DEFAULT_OUTPUT_DIRECTORY, scenario_name)
    if loop_output_directory == None:
        loop_output_directory = os.path.join(output_folder, "loop_outputs_"+str(variable_name))

    output = pd.DataFrame()
    # parse through scalars folder and read in all excel sheets
    for filepath in list(
        glob.glob(os.path.join(loop_output_directory, "scalars", "*.xlsx"))
    ):

        file_sheet1 = pd.read_excel(
            filepath, header=0, index_col=1, sheet_name="cost_matrix"
        )
        file_sheet2 = pd.read_excel(
            filepath, header=0, index_col=1, sheet_name="scalar_matrix"
        )
        file_sheet3 = pd.read_excel(
            filepath, header=0, index_col=0, sheet_name="scalars"
        )

        # get variable value from filepath
        i_split_one = filepath.split("_")[::-1][0]
        i = i_split_one.split(".")[0]

        # get all different pv assets
        csv_directory = os.path.join(output_folder, "mvs_outputs_loop_" + str(variable_name) + "_"+str(i), "inputs", "csv_elements")
        energyProduction = pd.read_csv(
            os.path.join(csv_directory, "energyProduction.csv"),
            index_col=0
        )
        energyProduction = energyProduction.drop(["unit"], axis=1)
        pv_labels = energyProduction.columns
        # get total costs pv and installed capacity
        for pv in pv_labels:
            output.loc[int(i), "costs total PV"] = file_sheet1.at[pv, "costs_total"]
            output.loc[int(i), "installed capacity PV"] = file_sheet2.at[
                pv, "optimizedAddCap"
            ]
            output.loc[int(i), "Total renewable energy use"] = file_sheet3.at[
                "Total renewable energy use", 0
            ]
            output.loc[int(i), "Renewable share"] = file_sheet3.at["Renewable_share", 0]
            output.loc[int(i), "LCOE PV"] = file_sheet1.at[
                pv, "levelized_cost_of_energy_of_asset"
            ]
            output.loc[int(i), "self consumption"] = file_sheet3.at[
                "Onsite energy fraction", 0
            ]
            output.loc[int(i), "self sufficiency"] = file_sheet3.at[
                "Onsite energy matching", 0
            ]
            output.loc[int(i), "Degree of autonomy"] = file_sheet3.at[
                "Degree of autonomy", 0
            ]

    output.sort_index(inplace=True)

    # plot
    fig = plt.figure()
    rows = len(kpi)
    num = (
        rows * 100 + 11
    )  # the setting for number of rows | number of columns | row number
    for i in kpi:
        ax = fig.add_subplot(num)
        num = num + 1
        output[i].plot(title=i, ax=ax, legend=False)

    fig.text(0.5, 0.0, str(variable_name), ha="center")
    plt.tight_layout()
    plt.show()

    fig.savefig(
        os.path.join(
            loop_output_directory, "plot_scalars_" + str(variable_name) + ".png"
        )
    )


if __name__ == "__main__":
    latitude = 52.5243700
    longitude = 13.4105300
    year = 2014  # a year between 2011-2013!!!
    population = 48000
    country = "Germany"
    scenario_name = "Scenario_A1"

    # loop(
    #     latitude=latitude,
    #     longitude=longitude,
    #     year=year,
    #     population=population,
    #     country=country,
    #     variable_name="specific_costs",
    #     variable_column="pv_plant_01",
    #     csv_file_variable="energyProduction.csv",
    #     start=500,
    #     stop=2000,
    #     step=100,
    #     output_directory=None,
    #     scenario_name=scenario_name
    # )

    # plot_all_flows(month=None, calendar_week=None, weekday=10)

    plot_kpi_loop(
        scenario_name=scenario_name,
        variable_name="specific_costs",
        kpi=[
            "costs total PV",
            "Degree of autonomy",
            "self consumption",
            "self sufficiency",
        ],
    )