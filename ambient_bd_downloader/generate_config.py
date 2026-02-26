config_template = """
[DEFAULT]
# Files and directories
client-id-file=.\\client_id.txt
download-dir=.\\downloaded_data
# Data scope
from-date=2021-01-01
zone=ABD Pilot
device=*
subject=*
exclude-subjects=*
            
[DOWNLOAD]
# Filtering
ignore-epoch-for-shorter-than-hours=2
flag-nights-with-sleep-under-hours=5

[QUALITY_REPORT]
min-distance=0.4
max-distance=1.5
min-signal-quality=4
max-fraction-no-presence=0.2
max-fraction-awake=0.3
min-session-separation=15
max-split-sessions=2
"""

def generate_config():
    with open('ambient_downloader.properties', 'w') as f:
        config = (config_template)
        f.write(config)
