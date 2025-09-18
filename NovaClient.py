# The following 'NovaClient' class is derived from the Astrometry.net software,
# which is licensed under the BSD 3-Clause License - see LICENSES/BSD-3-Clause.txt
#
# Copyright 2009 Dustin Lang
# https://github.com/dstndstn/astrometry.net

import json
from urllib.parse import urlencode, quote
from urllib.request import urlopen, Request
from urllib.error import HTTPError

if __name__ == "__main__":
    print("This is the NovaClient library and cannot be ran")

def json2python(data):
    try:
        return json.loads(data)
    except:
        pass
    return None

def python2json(pyd):
    return json.dumps(pyd)

class NovaClient(object):
    '''
    nova.astrometry.net client
    '''
    default_url = 'https://nova.astrometry.net/api/'

    def __init__(self, apiurl=default_url):
        self.session = None
        self.apiurl = apiurl

    def get_url(self, service):
        '''
        constructs URL for a plate-solver service
        '''
        return self.apiurl + service

    def send_request(self, service, args={}, file_args=None):
        '''
        service: string
        args: dict
        '''
        if self.session is not None:
            args.update({ 'session': self.session })
        # print 'Python:', (args)
        json = python2json(args)
        # print 'Sending json:', json
        url = self.get_url(service)
        print('Sending to URL:', url)
        # If we're sending a file, format a multipart/form-data
        if file_args is not None:
            import random
            boundary_key = ''.join([random.choice('0123456789') for _ in range(19)])
            boundary = '===============%s==' % boundary_key
            headers = {'Content-Type':
                       'multipart/form-data; boundary="%s"' % boundary}
            data_pre = (
                '--' + boundary + '\n' +
                'Content-Type: text/plain\r\n' +
                'MIME-Version: 1.0\r\n' +
                'Content-disposition: form-data; name="request-json"\r\n' +
                '\r\n' +
                json + '\n' +
                '--' + boundary + '\n' +
                'Content-Type: application/octet-stream\r\n' +
                'MIME-Version: 1.0\r\n' +
                'Content-disposition: form-data; name="file"; filename="%s"' % file_args[0] +
                '\r\n' + '\r\n')
            data_post = (
                '\n' + '--' + boundary + '--\n')
            data = data_pre.encode() + file_args[1] + data_post.encode()
        else:
            # Else send x-www-form-encoded
            data = {'request-json': json}
            # print 'Sending form data:', data
            data = urlencode(data).encode('utf-8')
            # print 'Sending data:', data
            headers = {}

        request = Request(url=url, headers=headers, data=data)
        try:
            fle = urlopen(request)
            txt = fle.read()
            # DEBUG print 'Got json:', txt
            result = json2python(txt)
            if not result:
                raise RequestError('Server did not send valid json: ', txt)
            # DEBUG print 'Got result:', result
            stat = result.get('status')
            # DEBUG print 'Got status:', stat
            if stat == 'error':
                errstr = result.get('errormessage', '(none)')
                raise RequestError('server error message: ' + errstr)
            return result
        except HTTPError as err:
            print('HTTPError', err)
            txt = err.read()
            errFileName = 'err.html'
            open(errFileName, 'wb').write(txt)
            print('Wrote error text to ', errFileName)

    def login(self, apikey):
        '''
        Logs us into the plate-solver and gets a session key
        '''
        import string
        args = { 'apikey': apikey.strip() }
        result = self.send_request('login', args)
        sess = result.get('session') if result is not None else None
        if not sess:
            raise RequestError('no session in result')
        print('Got session:', sess)
        self.session = sess

    def _get_upload_args(self, **kwargs):
        '''
        returns the specified solving options
        '''
        args = {}
        lkdt = [('allow_commercial_use', 'd', str),
                ('allow_modifications', 'd', str),
                ('publicly_visible', 'y', str),
                ('scale_units', None, str),
                ('scale_type', None, str),
                ('scale_lower', None, float),
                ('scale_upper', None, float),
                ('scale_est', None, float),
                ('scale_err', None, float),
                ('center_ra', None, float),
                ('center_dec', None, float),
                ('radius', None, float),
                ('downsample_factor', None, int),
                ('tweak_order', None, int),
                ('crpix_center', None, bool), ]
        for key, default, typ in lkdt:
            # image_width, image_height
            if key in kwargs:
                val = kwargs.pop(key)
                val = typ(val)
                args.update({key: val})
            elif default is not None:
                args.update({key: default})
        # print 'Upload args:', args
        return args

    def upload(self, fne, **kwargs):
        '''
        uploads an image file
        '''
        args = self._get_upload_args(**kwargs)
        try:
            fle = open(fne, 'rb')
            result = self.send_request('upload', args, (fne, fle.read()))
            return result
        except IOError:
            print('File %s does not exist' % fne)
            raise

    def myjobs(self):
        '''
        queries server for our jobs
        '''
        result = self.send_request('myjobs/')
        return result['jobs']

    def job_status(self, job_id, justdict=False):
        '''
        queries server to see if a job is finished
        '''
        result = self.send_request('jobs/%s' % job_id)
        if justdict:
            return result
        stat = result.get('status')
        if stat == 'success':
            return stat
        return stat

    def sub_status(self, sub_id, justdict=False):
        '''
        queries server for submission status
        '''
        result = self.send_request('submissions/%s' % sub_id)
        if justdict:
            return result
        return result.get('status')

    def jobs_by_tag(self, tag, exact):
        '''
        not sure what that does
        '''
        exact_option = 'exact=yes' if exact else ''
        result = self.send_request('jobs_by_tag?query=%s&%s'
                                   % (quote(tag.strip()), exact_option), {}, )
        return result
