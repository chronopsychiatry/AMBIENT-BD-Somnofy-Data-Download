def generate_config():
    with open('ambient_downloader.properties', 'w') as f:
        config = ('[DEFAULT]\n'
                  '# Files and directories\n'
                  'credentials-file=.\\somnofy_credentials.txt\n'
                  'download-dir=.\\downloaded_data\n'
                  '# Data scope\n'
                  'from-date=2021-01-01\n'
                  'zone=ABD Pilot\n'
                  'device=*\n'
                  'subject=*\n'
                  '# Filtering\n'
                  'ignore-epoch-for-shorter-than-hours=2\n'
                  'flag-nights-with-sleep-under-hours=5'
                  )
        f.write(config)
