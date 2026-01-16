# AmbientBD Somnofy data download

This a package for downloading sleep data from the radar devices and storing them in an "analysis friendly" format.

## Installation

### Setting up the environment

We recommend using [Anaconda](https://www.anaconda.com/download/) to manage your Python environment. Once you have Anaconda installed, you can create a new python environment by running the following command:

```bash
conda create -n ambient python=3.12
```

Activate the environment by running:

```bash
conda activate ambient
```

### Installing the package

Install from the Python Package Index repository with the command:

```bash
pip install ambient_bd_downloader
```

## Using the package

Remember to activate the environment first (`conda activate ambient`).

### Configuration

On the first run, a properties file needs to be generated. To do this, run the command:

```bash
ambient_generate_config
```

This will create a file `ambient_downloader.properties` in the current directory.

Open the properties file with a text editor to change the parameters (description below).

#### Files and directories

##### client-id-file

Path to the the `.txt` file containing the client ID. The file must only contain the client ID.

Default value: `./client_id.txt`

##### download-dir

Folder in which the data will be downloaded

Default value: `./downloaded_data`

#### Data scope

##### from-date

The date from which to download data, in ISO format `YYYY-MM-DD`.

The program remembers the last downloaded session (for each study subject ) and continues download from there. Check below for more details on how to force the download of all sessions.

##### zone

The zone name(s) from which to download data. Multiple zones can be provided, separated by commas `,`. `zone=*` will download data from all available zones.

##### device

The device id(s) from which to download data. Multiple devices can be provided, separated by commas `,`. `device=*` will download data from all available devices.

##### subject

The subject identifier(s) from which to download data. Multiple subjects can be provided, separated by commas `,`. `subject=*` will download data from all available subjects.

#### Filtering

##### ignore-epoch-for-shorter-than-hours

Somnofy creates a new session everytime someone enters the room. These sessions are not useful for the analysis and can be filtered out from the epoch data. This parameter can be used to filter out the sessions shorter than the specified number of hours. These sessions will not be included in the epoch data but still visible in the session reports.

##### flag-short-sleep-for-less-than-hours

To help checking the compliance of the data capture process, the total hours of sleep are calculated for each night. If the total sleep time is less than the specified hours, the session is flagged as INVALID. This parameter can be used to set the threshold for the short sleep flag.

### Download data

To download the data, navigate to the folder that contains the `ambient_downloader.properties` file, and run the following command:

```bash
ambient_download
```

## General behaviour

In the typical use, the program is run periodically (by a researcher or automatically) to download the data from the Somnofy server. The program remembers the last downloaded session for each subject and continues the download from there. For each run a new set of output files is generated and marked with the date range of the download (last_session date to current date).

It is recommended to run the program in the afternoon so all the "sleep" sessions will be terminated, as the program ignores the "in progress" sessions.

All raw data are stored in json files as retrieved from Somnofy.

The epoch data are the timeseries of the monitored variables, with time value in the timestamp column. They are called epoch because they contain aggregated data from the 30s epochs.

In the initial cleaning, the short sessions are filtered out from the epoch data. The short sessions are those which are shorter than the specified hours in the `ignore-epoch-for-shorter-than-hours` parameter in the `ambient_downloader.properties` file.

The compliance report is being generated for each night within the download date range. The compliance report contains for example the number of sessions, total sleep time and the flag VALID. The night is considered valid if the total sleep time is greater than the specified hours in the `flag-short-sleep-for-less-than-hours` parameter in the `ambient_downloader.properties` file.

### Monitoring program porgress

The program outputs the current operations or errors to both the console and the log file.
The log file is stored in the download directory as `download.log`.

## Data layout and format

Example folder structure for 2 subjects (U03, U04) in zone "ABD Test" and 2 download program runs
on 2024-07-26 and 2024-08-03. There were no data for subject U03 after 26th July.

```default
- downloaded_data
    - ABD Test
        - U03-66744b82056bcf001afa8d69
            - data
                - 2024-07-14_2024-07-26_epoch_data.csv
                - 2024-07-14_2024-07-26_session_report.csv
                - 2024-07-14_2024-07-26_compliance_info.csv
            - raw
                - 2024-07-14_WUVFRRgHDg4RAgAA.json
                - 2024-07-14_WUVFRRgHDgkCIgAA.json
                - ...
            - sys
                - last_session.json
        - U04-66826ea1056bcf001afdfca1
            - data
                - 2024-07-14_2024-07-26_epoch_data.csv
                - 2024-07-14_2024-07-26_session_report.csv
                - 2024-07-14_2024-07-26_compliance_info.csv
                - 2024-07-27_2024-08-03_epoch_data.csv
                - 2024-07-27_2024-08-03_session_report.csv
                - 2024-07-27_2024-08-03_compliance_info.csv
            - raw
                - 2024-07-15_WUdIQhgHDxYHIgAA.json
                - ...
            - sys
                - last_session.json

```

For each subject a folder is created in the download folder. The folder name is a combination of the subject identifier and subject ID. For example, if a subject has identifier `abd1234` and ID `sub_01J9VDRPY3PAJ12K1N3C4M3JMF`, the folder name would be `abd1234-sub_01J9VDRPY3PAJ12K1N3C4M3JMF`. Inside the subject folder, there are three subfolders: `data`, `raw` and `sys`.

The `sys` folder contains the information used by the program to track the download status. For example it stores the last finished session which has been downloaded. This information is used when download is restarted to continue from the last session.

The `raw` folder contains the raw data downloaded from the Somnofy server. The data is stored in `json` format. Each session is stored in a separate file. The file name is the DATE-SESSION_ID.json.
That way the raw data can be sorted by date.

The `data` folder contains the epoch data and sessions report in an *easy* to use form as data tables. The data is stored in `csv` format.
Whenever the download is started, the date range is established as START_DATE_OF_THE_FIRST_DOWNLOADED_SESSION to the END_DATE_OF_THE_LAST_FINISHED session.

For example if in the previous run the last downloaded session terminates on 2024-07-14 at 9:30, we run download in the afternoon of the 2024-07-26
the program will use as the date range: `2024-07-14_2024-07-26` (if there was a session on the 26th July).

The date-range is used to name the following files:

```default
- 2024-07-14_2024-07-26_epoch_data.csv - with the epoch data within the date range
- 2024-07-14_2024-07-26_session_report.csv - with the list of sessions and their characteristics in the date range
- 2024-07-14_2024-07-26_compliance_info.csv - with the information on the validy of each night in the date range 
```

Additionally, the file `all_sessions_report.csv` contains characteristics of all the sessions ever downloaded by the program, which can be used to find sessions for any day within the study.

### Epoch data

The epoch-data file contains the timeseries of the monitored variables for each session within the download date range (remember only the sessions with duration larger than `ignore-epoch-for-shorter-than-hours` are included).

The epoch data contains the following columns:

| Column Name                  | Description                                                         |
|------------------------------|---------------------------------------------------------------------|
| `timestamp`                  | The timestamp of the 30 second epoch for which data row is created. |
| `session_id`                 | The Somnofy's unique identifier for the session.                    |
| `signal_quality_mean`        | The mean signal quality during the epoch.                           |
| `respiration_rate_mean`      | The mean respiration rate during the epoch.                         |
| `respiration_rate_var`       | The variance of the respiration rate during the epoch.              |
| `movement_fast_mean`         | The mean movement detected during the epoch.                        |
| `movement_fast_nonzero_pct`  | The percentage of non-zero values for fast movement during the      |
| `heart_rate_mean`            | The mean heart rate during the epoch.                               |
| `heart_rate_var`             | The variance of the heart rate during the epoch.                    |
| `external_heart_rate_mean`   | The mean external heart rate during the epoch.                      |
| `external_heart_rate_var`    | The variance of the external heart rate during the epoch.           |
| `external_spo2_mean`         | The mean external SpO2 level during the epoch.                      |
| `external_spo2_var`          | The variance of the external SpO2 level during the epoch.           |
| `distance_mean`              | The mean distance to subject measured during the epoch.             |
| `motion data count`          | The number of data points in the epoch (30).                        |
| `light_ambient_mean`         | The ambient light level during the epoch.                           |
| `sound_amplitude_mean`       | The sound amplitude during the epoch.                               |
| `temperature_ambient_mean`   | The ambient temperature during the epoch.                           |
| `pressure_mean`              | The mean atmospheric pressure during the epoch.                     |
| `humidity_mean`              | The mean humidity value during the epoch                            |
| `indoor_air_quality_mean`    | The mean indoor air quality during the epoch                        |
| `epoch_duration`             | The precise duration of the epoch (seconds)                         |
| `sleep_stage`                | The sleep stage as calculated by the VitalThings algorithm. 1 = Deep sleep, 2 = Light sleep, 3 = REM, 4 = Awake, 5 = No presence |

### Compliance info

The compliance info file contains rows for each nights within the download date range with characteristics that help assess the validity of the sleep data, for example if the number of sessions is 0 the sensor must have been offline.

The compliance info contains the following columns:

| Column Name                | Description                                                                                                            |
|----------------------------|------------------------------------------------------------------------------------------------------------------------|
| `night_date`               | The date of the night for which sessions are being assessed. All sessions which end at this date are included.         |
| `number_of_long_sessions`  | The number of sessions longer than the minimal duration specified in `ignore-epoch-for-shorter-than-hours`.            |
| `max_time_in_bed_h`        | The maximum time spent in bed during the night, in hours                                                               |
| `max_time_asleep_h`        | The maximum time spent asleep during the night, in hours.                                                              |
| `total_sleep_time_h`       | The total sleep time during the night, in hours. Calculated with time asleep for all not ignored session in this night |
| `valid`                    | True if the night is valid, which currently means: (a) there are recordings for this date, and (b) the total sleep is >= `flag-short-sleep-for-less-than-hours` |

### Session report

The session report file contains rows for ALL session within the download date range (they are not filtered with ignore).

Apart from housekeeping information about the session (id, session_start, session_end), it contains the information about the sleep and activity.

| Column Name                          | Description                                                  |
|--------------------------------------|--------------------------------------------------------------|
| `id`                                 | The somnofy unique identifier for the session.               |
| `state`                              | Indicates if the session is ENDED or IN-PROGRESS             |
| `subject_id`                         | The unique ID of the subject associated with this session.   |
| `device_serial_number`               | Serial number of the Somnofy device which recorded the session.|
| `epoch_count`                        | The number of 30s epochs in the session.                     |
| `session_start`                      | The timestamp for start of the session.                      |
| `relative_session_start`             | @TODO check somnofy                                          |
| `session_end`                        | The timestamp for end of the session.                        |
| `time_at_last_epoch`                 | The timestamp  the last epoch of the session.                |
| `time_at_intended_sleep`             | The time of sleep attempt.                                   |
| `time_at_intended_wakeup`            | @TODO CHECK SOMNOFY                                          |
| `time_in_undefined`                  | The time spent in undefined (sleep) stage.                   |
| `time_at_sleep_onset`                | The fall asleep time.                                        |
| `time_at_wakeup`                     | The wakeup time.                                             |
| `time_at_midsleep`                   | Time at the mid-point between sleep onset and wakeup.        |
| `sleep_onset_latency`                | The time it took to fall asleep in seconds.                  |
| `sleep_period`                       | The duration of the sleep session [s].                       |
| `time_in_bed`                        | The total time spent in bed [s].                             |
| `time_asleep`                        | The total time scored as asleep in the session [s].          |
| `sleep_efficiency`                   | The efficiency of sleep.                                     |
| `time_in_light_sleep`                | The time spent in light sleep [s].                           |
| `time_in_rem_sleep`                  | The time spent in REM sleep [s].                             |
| `time_in_deep_sleep`                 | The time spent in deep sleep [s].                            |
| `time_in_no_presence`                | The time spent with no presence detected [s]                 |
| `number_of_times_no_presence`        | The number of times no presence was detected.                |
| `time_wake_after_sleep_onset`        | The time spent awake after sleep onset.                      |
| `number_of_times_awake`              | The number of times the subject woke up.                     |
| `number_of_times_awake_long`         | The number of times the subject woke up for a long duration. |
| `time_wake_pre_post_sleep`           | The time spent awake before and after sleep.                 |
| `time_from_sleep_onset_to_first_rem` | The period of REM sleep onset.                               |
| `movement_fast_during_sleep_period_mean` | The mean movement during sleep.                          |
| `rpm_non_rem_filtered_mean`          | The mean RPM (respirations per minute) during non-REM sleep. |
| `rpm_non_rem_mean_var`               | Variance of the RPM during non-REM sleep.                    |
| `rpm_non_rem_baseline`               | Baseline of the RPM during non-REM sleep.                    |
| `rpm_non_rem_baseline_std`           | Standard deviation of the baseline of the RPM during non-REM sleep. |
| `heart_rate_non_rem_filtered_mean`   | The mean heart rate during non-REM sleep.                    |
| `heart_rate_non_rem_mean`            | The non-filtered mean heart rate during non-REM sleep.       |
| `external_heart_rate_non_rem_filtered_mean` | The mean external heart rate during non-REM sleep.    |
| `epochs_with_movement_pct`           | The percentage of epochs with movement.                      |
| `epochs_with_movement_during_time_in_bed_pct` | The percentage of epochs with movement while in bed.|
| `time_with_movement_pct`             | The percentage of time with movement.                        |
| `time_with_movement_during_time_in_bed_pct` | The percentage of time in bed with movement.          |
| `sleep_cycle_count`                  | Number of sleep cycles in the session.                       |
| `is_workday`                         | Whether the session was on a work day                        |
| `chronotype`                         | The chronotype for this session, i.e. the time at mid-sleep, in hours. |
| `social_jet_lag`                     | @TODO: CHECK SOMNOFY                                         |
| `jet_lag`                            | @TODO: CHECK SOMNOFY                                         |
| `regularity`                         | @TODO: CHECK SOMNOFY                                         |
| `sleep_score_standard`               | The sleep score based on the standard scoring method.        |
| `sleep_fragmentation`                | @TODO: CHECK SOMNOFY                                         |
| `external_spo2_mean`                 | The mean external SpO2 level.                                |
| `external_spo2_min`                  | The minimum external SpO2 level.                             |
| `distance_during_sleep_mean`         | Mean distance from the sensor during sleep.                  |
| `distance_during_sleep_std`          | Standard deviation of the distance from sensor during sleep. |
| `air_pressure_filtered_mean`         | The filtered mean air pressure.                              |
| `light_ambient_filtered_mean`        | The filtered mean ambient light level.                       |
| `light_ambient_at_wakeup_mean`       | The mean ambient light level at wake-up time.                |
| `sound_amplitude_filtered_mean`      | The filtered mean sound amplitude.                           |
| `sound_amplitude_during_sleep_filtered_for_noise_mean`| The mean sound amplitude during sleep, filtered for noise. |
| `sound_amplitude_during_sleep_filtered_for_movement_mean`| The mean sound amplitude during sleep, filtered for movement. |
| `sound_amplitude_at_wake_up`         | The sound amplitude at wake-up time.                         |
| `epochs_with_sound_spikes_during_sleep_count` | Number of epochs that had sound spikes during sleep.|
| `awakenings_caused_by_sound_count`   | Number of awakenings caused by sound.                        |
| `temperature_filtered_mean`          | The filtered mean temperature.                               |
| `indoor_air_quality_filtered_mean`   | The filtered mean indoor air quality.                        |
| `air_humidity_filtered_mean`         | The filtered mean air humidity.                              |

### All sessions report

Is the same as session_report but contains all the sessions ever downloaded by the program. It can be used for example to find sessions for any day within the study.
