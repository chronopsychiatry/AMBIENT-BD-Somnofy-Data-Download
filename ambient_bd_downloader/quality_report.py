import logging
import pkg_resources

from ambient_bd_downloader.download.data_download import DataDownloader
from ambient_bd_downloader.sf_api.somnofy import Somnofy
from ambient_bd_downloader.storage.paths_resolver import PathsResolver
from ambient_bd_downloader.download.quality_checker import QualityChecker
from ambient_bd_downloader.properties.properties import load_application_properties

def quality_report():
    """
    Generate a report on data quality (accesses data through the API but does not download it)
    """

    properties = load_application_properties()

    # Configure the logger
    if not properties.download_folder.exists():
        properties.download_folder.mkdir(parents=True)
    logging.basicConfig(
        level=logging.INFO,  # Set the log level
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log format
        handlers=[
            logging.FileHandler(properties.download_folder / "data_quality.log"),  # Log to a file
            logging.StreamHandler()  # Log to console
        ]
    )

    logger = logging.getLogger('main')
    version = pkg_resources.require("ambient-bd-downloader")[0].version
    logger.info(f'Running ambient_bd_downloader version {version}')
    logger.info(f'Properties: {properties}')
    
    logger.info(f'Accessing somnofy with client ID stored at: {properties.client_id_file}')
    somnofy = Somnofy(properties)
    qc = QualityChecker(
        min_distance=properties.min_distance,
        max_distance=properties.max_distance,
        min_signal_quality=properties.min_signal_quality,
        max_fraction_no_presence=properties.max_fraction_no_presence,
        max_fraction_awake=properties.max_fraction_awake,
        min_session_separation=properties.min_session_separation,
        max_split_sessions=properties.max_split_sessions
    )

    zones_to_access = somnofy.get_all_zones() if properties.zone_name == ['*'] else properties.zone_name

    for zone in zones_to_access:
        if somnofy.has_zone_access(zone):
            logger.info(f'Accessing somnofy zone "{zone}"')
        else:
            logger.info(f'Access to zone "{zone}" denied.')
            continue

        subjects = somnofy.select_subjects(zone_name=zone,
                                           subject_name=properties.subject_name,
                                           exclude_subjects=properties.exclude_subjects,
                                           device_name=properties.device_name)
        for u in subjects:
            logger.info(f"{u}")

        resolver = PathsResolver(properties.download_folder / zone)
        downloader = DataDownloader(somnofy, resolver=resolver, qc=qc)

        downloader.save_quality_reports(subjects, properties.from_date)
