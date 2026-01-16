import logging
import pkg_resources

from ambient_bd_downloader.download.data_download import DataDownloader
from ambient_bd_downloader.sf_api.somnofy import Somnofy
from ambient_bd_downloader.storage.paths_resolver import PathsResolver
from ambient_bd_downloader.properties.properties import load_application_properties


def main():
    properties = load_application_properties()

    # Configure the logger
    if not properties.download_folder.exists():
        properties.download_folder.mkdir(parents=True)
    logging.basicConfig(
        level=logging.INFO,  # Set the log level
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log format
        handlers=[
            logging.FileHandler(properties.download_folder / "download.log"),  # Log to a file
            logging.StreamHandler()  # Log to console
        ]
    )

    logger = logging.getLogger('main')
    version = pkg_resources.require("ambient-bd-downloader")[0].version
    logger.info(f'Running ambient_bd_downloader version {version}')
    logger.info(f'Properties: {properties}')

    from_date = properties.from_date

    logger.info(f'Accessing somnofy with client ID stored at: {properties.client_id_file}')
    somnofy = Somnofy(properties)

    zones_to_access = somnofy.get_all_zones() if properties.zone_name == ['*'] else properties.zone_name

    for zone in zones_to_access:
        if somnofy.has_zone_access(zone):
            logger.info(f'Accessing somnofy zone "{zone}"')
        else:
            logger.info(f'Access to zone "{zone}" denied.')
            continue

        subjects = somnofy.select_subjects(zone_name=zone,
                                           subject_name=properties.subject_name,
                                           device_name=properties.device_name)
        for u in subjects:
            logger.info(f"{u}")

        resolver = PathsResolver(properties.download_folder / zone)
        downloader = DataDownloader(somnofy, resolver=resolver,
                                    ignore_epoch_for_shorter_than_hours=properties.ignore_epoch_for_shorter_than_hours,
                                    filter_shorter_than_hours=properties.flag_nights_with_sleep_under_hours)

        for u in subjects:
            downloader.save_subject_data(u, from_date)


if __name__ == '__main__':
    main()
