"""Refresh the bundled license texts from licenses-db.

Run with ``python -m oscad_data.download``.
"""
import os
from urllib.request import urlopen

from oscad_data import load_data

texts_dir = os.path.join(os.path.dirname(__file__), 'data', 'texts')
baseurl = 'https://raw.githubusercontent.com/enyst/licenses-db/master/'
TIMEOUT = 30


def main():
    details = load_data('license_details')

    for oscad_id, detail in details.items():
        licensedb_id = detail['licensedb_id']
        url = baseurl + licensedb_id + '.txt'

        with urlopen(url, timeout=TIMEOUT) as response:
            if response.status != 200:
                raise RuntimeError(
                    '%s returned HTTP %s' % (url, response.status))
            content = response.read()

        with open(os.path.join(texts_dir, licensedb_id + '.txt'), 'wb') as f:
            f.write(content)

        link = os.path.join(texts_dir, oscad_id + '.txt')
        if oscad_id != licensedb_id and not os.path.lexists(link):
            os.symlink(licensedb_id + '.txt', link)


if __name__ == '__main__':
    main()
