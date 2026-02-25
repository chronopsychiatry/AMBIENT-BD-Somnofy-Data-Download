import numpy as np

from ambient_bd_downloader.storage.paths_resolver import PathsResolver
from ambient_bd_downloader.sf_api.somnofy import Somnofy

class QualityChecker:
    """
    Run quality checks on the Somnofy data and output flagged sessions in csv format
    """
    def __init__(self,
                 min_distance=0.4,
                 max_distance=1.5,
                 min_signal_quality=4,
                 max_fraction_no_presence=0.2,
                 max_fraction_awake=0.3,
                 min_session_separation=15):
        self._logger = logging.getLogger('QualityChecker')
        
    def get_flags(session_json):
        flags = set()
        dist = session_json.get('distance_during_sleep_mean')
        # Signal quality: calculate % of points under threshold
        signal_quality = session_json.get('epoch_data').get('signal_quality_mean')

        if (dist < min_distance) or (dist > max_distance):
            flags.add("distance")

        if sum(signal_quality < 4) > (0.8 * length(signal_quality)):
            flags.add("signal_quality")
