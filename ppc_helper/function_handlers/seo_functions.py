import requests


def seo_check_urls_status_code(data):
    """
    Check status code of given urls
    :param urls: comma separated urls
    :return: list of rows
    """
    urls = data['data']
    urls = urls.replace(' ', '')
    sep = '\n' if '\n' in urls else ','
    urls = urls.split(sep)
    urls = [u.split('?')[0] for u in urls]
    output = [['start_url', 'finish_url', 'response_code', 'redirects(in order)']]
    for u in urls:
        try:
            r = requests.get(u)
            redirects = ';'.join([i.url for i in r.history])
            output.append([u, r.url, r.status_code, redirects])
        except Exception:
            output.append([u, 'Unable to connect', 0, 0])
    return output

