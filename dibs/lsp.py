'''
lsp.py: DIBS interface to LSPs.

Copyright
---------

Copyright (c) 2021-2022 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from   abc import ABC, abstractmethod
from   coif import cover_image
from   commonpy.network_utils import net
from   dataclasses import dataclass
from   os.path import join, exists
import pokapi
from   pokapi import Folio
import re
from   sidetrack import log
from   textwrap import wrap
from   topi import Tind
from urllib.error import HTTPError, URLError
import jwt
from datetime import datetime, timedelta

from .settings import config, resolved_path
import urllib.request
import urllib.parse
import simplejson
import sys
from pickle import NONE


# Classes implementing interface to specific LSPs.
# .............................................................................

@dataclass
class LSPRecord():
    '''Common abstraction for records returned by different LSP's.'''
    item_id   : str
    item_page : str
    title     : str
    author    : str
    publisher : str
    edition   : str
    year      : str
    isbn_issn : str


class LSPInterface(ABC):
    '''Abstract interface class for getting a record from an LSP.

    All concrete implementations of this class are assumed to have at least
    a URL for the API of the server, and may have additional parameters on
    a per-class basis.
    '''

    def __init__(self, url = None):
        '''Create an interface for the server at "url".'''
        self.url = url


    def __repr__(self):
        '''Return a string representing this interface object.'''
        return "<{} for {}>".format(self.__class__.__name__, self.url)


    @property
    @abstractmethod
    def name(self):
        '''Return the name of this LSP, for use in (e.g.) error messages.'''
        pass                            # noqa: PIE790


    @abstractmethod
    def record(self, barcode = None):
        '''Return a record for the item identified by the "barcode".'''
        pass                            # noqa: PIE790

    @abstractmethod
    def setstatus(self, barcode = None, ready = True):
        '''Return a record for the item identified by the "barcode".'''
        pass                            # noqa: PIE790


class TindInterface(LSPInterface):
    '''Interface layer for TIND hosted LSP servers.'''

    def __init__(self, url = None, thumbnails_dir = None):
        '''Create an interface for the server at "url".'''
        self.url = url
        self._thumbnails_dir = thumbnails_dir
        self._tind = Tind(url)


    @property
    def name(self):
        '''Return the name of this LSP, for use in (e.g.) error messages.'''
        return 'TIND'


    def record(self, barcode = None):
        '''Return a record for the item identified by the "barcode".'''
        try:
            rec = self._tind.item(barcode = barcode).parent
            title = rec.title
            if rec.subtitle:
                title += ': ' + rec.subtitle
            log(f'record for {barcode} has id {rec.tind_id} in {self.url}')
            thumbnail_file = join(self._thumbnails_dir, barcode + '.jpg')
            # Don't overwrite existing images.
            if not exists(thumbnail_file):
                if rec.thumbnail_url:
                    save_thumbnail(thumbnail_file, url = rec.thumbnail_url)
                elif rec.isbn_issn:
                    save_thumbnail(thumbnail_file, isbn = rec.isbn_issn)
                else:
                    log(f"{barcode} lacks ISBN & thumbnail URL => no thumbnail")
            else:
                log(f'thumbnail image already exists in {thumbnail_file}')
            return LSPRecord(item_id   = rec.tind_id,
                             item_page = rec.tind_url,
                             title     = truncated_title(rec.title),
                             author    = rec.author,
                             publisher = rec.publisher,
                             year      = rec.year,
                             edition   = rec.edition,
                             isbn_issn = rec.isbn_issn)
        except Exception:
            log(f'could not find {barcode} in TIND')
            raise ValueError('No such barcode {barcode} in {self.url}')


class SolrInterface(LSPInterface):
    '''Interface layer for TIND hosted LSP servers.'''

    def __init__(self, url = None):
        '''Create an interface for the server at "url".'''
        self.url = url
        # self.host = "virgo4-solr-staging-replica-1-private.internal.lib.virginia.edu"
        # self.port = "8080"
        # self.collection = "test_core"
        # self.qt         = "select"
        # self.url        = 'https://' + host + ':' + port + '/solr/' + collection + '/' + qt + '?'

        self.fl         = "fl=id,full_title_a,author_a,published_display_a,publisher_name_a,isbn_a,issn_a"
        self.fq         = "fq=data_source_f:sirsi"
        self.rows       = "rows=1"
        self.wt         = "wt=json"
        self.params     = [ self.fl, self.fq, self.wt, self.rows ]
        self.p          = "&".join(self.params)


    def record(self, barcode = None):
        '''Return a record for the item identified by the "barcode".'''
        try:
            rec = self.finditem(barcode = barcode)
            doc0 = rec['response']['docs'][0]
            rec_id = doc0['id']
            title = doc0.get('full_title_a', [''])[0]
            author = doc0.get('author_a', [''])[0]
            year = doc0.get('published_display_a', [''])[0]
            publisher = doc0.get('publisher_name_a', [''])[0]
            isbn = doc0.get('isbn_a', [''])[0]
            issn = doc0.get('issn_a', [''])[0]
            isbn_issn = isbn or issn
            edition = ''
            url = f'https://search.lib.virginia.edu/items/{rec_id}'

            log(f'record for {barcode} has id {rec_id} in {self.url}')
            log(f'record for {barcode} has title {title}')
            log(f'record for {barcode} has suthor {author}')
            log(f'record for {barcode} has year {year}')
            log(f'record for {barcode} has publisher {publisher}')

            #thumbnail_file = join(self._thumbnails_dir, barcode + '.jpg')
            # Don't overwrite existing images.
            #if not exists(thumbnail_file):
            #    if rec.thumbnail_url:
            #        save_thumbnail(thumbnail_file, url = rec.thumbnail_url)
            #    elif rec.isbn_issn:
            #        save_thumbnail(thumbnail_file, isbn = rec.isbn_issn)
            #    else:
            #        log(f"{barcode} lacks ISBN & thumbnail URL => no thumbnail")
            #else:
            #    log(f'thumbnail image already exists in {thumbnail_file}')
            record = LSPRecord(id        = rec_id,
                               url       = url,
                               title     = truncated_title(title),
                               author    = author,
                               publisher = publisher,
                               year      = year,
                               edition   = edition,
                               isbn_issn = isbn_issn)
            return record
        except Exception:
            log(f'could not find {barcode} in SOLR')
            raise ValueError('No such barcode {barcode} in {self.url}')

    def finditem(self, barcode = None):
        '''perform search on solr looking for item with barcode "barcode".'''
        try:
            q=f'q=barcode_e:{barcode}'
            full_url=self.url+'?'+self.p+'&'+q
            connection = urllib.request.urlopen(full_url)
            log(f'response {connection}')
            response   = simplejson.load(connection)
            #response = None
            return response
        except Exception:
            log(f'could not find {barcode} in SOLR')
            raise ValueError('No such barcode {barcode} in {self.url}')


class VirgoAPIInterface(LSPInterface):
    '''Interface layer for TIND hosted LSP servers.'''

    def __init__(self, url = None, urlAuth = None, urlStatus = None, secret = None):
        '''Create an interface for the server at "url".'''
        self.urlAuth = urlAuth
        self.secret = secret
        self.urlPool = url
        self.urlStatus = urlStatus
        self.authKey = None

    @property
    def name(self):
        '''Return the name of this LSP, for use in (e.g.) error messages.'''
        return 'VIRGO'

    def record(self, barcode = None):
        '''Return a record for the item identified by the "barcode".'''
        try:
            rec = self.finditem(barcode = barcode)
            fields = rec['fields']
            author = ""
            year = ""
            publisher = ""
            title = ""
            isbn = None
            issn = None
            for i,d in enumerate(fields):
                if d["name"] == "title_subtitle_edition" :
                    title = d["value"]
                elif (( d["name"] == "creator" or d["name"] == "author" ) and author == "" ):
                    author = d["value"]
                elif d["name"] == "published_date" :
                    year =  d["value"]
                elif d["name"] == "id" :
                    rec_id = d["value"]
                elif d["name"] == "publisher_name" :
                    publisher = d["value"]
                elif ( d["name"] == "isbn" and d["value"].startswith("978") ) :
                    isbn = d["value"]
                elif d["name"] == "issn" :
                    issn = d["value"]
            isbn_issn = isbn or issn or ""
            edition = ""
            url = f'https://search.lib.virginia.edu/items/{rec_id}'

            log(f'record for {barcode} has id {rec_id} in {self.urlPool}')
            log(f'record for {barcode} has title {title}')
            log(f'record for {barcode} has suthor {author}')
            log(f'record for {barcode} has year {year}')
            log(f'record for {barcode} has publisher {publisher}')
            #thumbnail_file = join(self._thumbnails_dir, barcode + '.jpg')
            # Don't overwrite existing images.
            #if not exists(thumbnail_file):
            #    if rec.thumbnail_url:
            #        save_thumbnail(thumbnail_file, url = rec.thumbnail_url)
            #    elif rec.isbn_issn:
            #        save_thumbnail(thumbnail_file, isbn = rec.isbn_issn)
            #    else:
            #        log(f"{barcode} lacks ISBN & thumbnail URL => no thumbnail")
            #else:
            #    log(f'thumbnail image already exists in {thumbnail_file}')
            record = LSPRecord(item_id   = rec_id,
                               item_page = url,
                               title     = truncated_title(title),
                               author    = author,
                               publisher = publisher,
                               year      = year,
                               edition   = edition,
                               isbn_issn = isbn_issn)
            return record
        except ValueError as ex:
            raise ex
        except Exception as ex:
            log(f'could not find {barcode} in SOLR')
            raise ValueError('No such barcode {barcode} in {self.url}')

    def finditem(self, barcode = None):
        '''perform search on solr looking for item with barcode "barcode".'''
        try:
            ''' get authorization key '''
            self.getGuestAuthKey()
            ''' use authorization key to do search by barcode '''
            log(f'submitting query for barcode {barcode} to URL {self.urlPool}')
            args = f'{{"query":"identifier: {{{barcode}}}","pagination":{{"start":0,"rows":10}},"filters":[]}}'
            headers = dict( [
                [ "Authorization", f'Bearer {self.authKey}' ],
                [ "Content-Type", "application/json" ]
                ] )
            argsdata = args.encode("utf-8")
            search_url = self.urlPool+'/search'+'?debug=1&verbose=1'
            request = urllib.request.Request(url = search_url, data = argsdata, headers = headers, method = "POST")
            log(f'headers {request.headers}')
            log(f'data {request.data}')
            log(f'search_url {search_url}')
            connection = urllib.request.urlopen(request)
            log(f'status = {connection.status}')
            response = simplejson.load(connection)
            lod = response["group_list"][0]["record_list"][0]["fields"]
            ididx = None
            for count, ele in enumerate(lod):
                if (ele["name"] == "id"):
                    ididx = count
            idval = lod[ididx]["value"]

            ''' use catkey to get item data '''
            ''' curl -vv -X GET "https://pool-solr-ws-uva-library.internal.lib.virginia.edu/api/resource/u2915688" -H "Content-Type: application/json" -H "Authorization: Bearer $AUTH_TOKEN"'''
            log(f'submitting request for resource {idval} to URL {self.urlPool}')
            item_url = self.urlPool+'/resource/'+idval
            log(f'item_url {item_url}')
            request = urllib.request.Request(url = item_url, data = None, headers = headers, method = "GET")
            connection = urllib.request.urlopen(request)
            log(f'status = {connection.status}')
            response = simplejson.load(connection)

            #response = None
            return response
        except KeyError :
            log(f'could not find {barcode} in SOLR')
            raise ValueError('No such barcode {barcode} in {self.url}')
        except HTTPError as ex:
            log(f'Error connecting to Sirsi to find data about {barcode}')
            log(f'status is {ex.status}')
            log(f'message is {ex.msg}')
            raise ValueError(f'{ex.status} {ex.msg} while connecting to Sirsi to find data about {barcode}'  )
        except URLError as ex:
            log(f'Error connecting to Sirsi to find data about {barcode}')
            log(f'message is {ex.reason.strerror}')
            raise ValueError(f'{ex.reason.strerror} while connecting to Sirsi to find data about {barcode}'  )
        except Exception as ex:
            exceptionMessage = repr(ex)
            log(f'exceptionMessage {exceptionMessage}')
            raise ex

    def setstatus(self, barcode = None, ready = True):
        '''perform search on solr looking for item with barcode "barcode".'''
        try:
            if (self.urlStatus != None):
                ''' get authorization key '''
                self.getGuestAuthKey()
                ''' use authorization key to do search by barcode '''
                log(f'setting status for {barcode} to URL {self.urlStatus}')

                headers = dict( [
                    [ "Authorization", f'Bearer {self.authKey}' ],
                    [ "Content-Type", "application/json" ]
                    ] )
                dibsstr = 'indibs' if ready else 'nodibs'
                status_url = self.urlStatus+'/dibs/'+dibsstr+'/'+barcode
                request = urllib.request.Request(url = status_url, headers = headers, method = "PUT")
                log(f'headers {request.headers}')
                log(f'set_status_url {status_url}')
                connection = urllib.request.urlopen(request)
                log(f'status = {connection.status}')
        except HTTPError as ex:
            log(f'Error setting status for {barcode} in Sirsi')
            log(f'status is {ex.status}')
            log(f'message is {ex.msg}')
            raise ValueError(f'{ex.status} {ex.msg} setting status for {barcode} in Sirsi'  )
        except Exception as ex:
            exceptionMessage = repr(ex)
            log(f'exceptionMessage {exceptionMessage}')
            raise ex

    def checkout_item(self, barcode = None, username = None, checkout = True, duration = 0):
        '''perform search on solr looking for item with barcode "barcode".'''
        try:
            if (self.urlStatus != None):
                ''' get authorization key '''
                self.getAuthKeyForPerson(username = username)
                ''' use authorization key to do search by barcode '''
                log(f'sending checkout request to Sirsi for barcode {barcode} for user {username}')
                args = f'{{"duration": "{duration}", "user_id" : "{username}", "barcode" : "{barcode}"}}'
                argsdata = args.encode("utf-8")

                headers = dict( [
                    [ "Authorization", f'Bearer {self.authKey}' ],
                    [ "Content-Type", "application/json" ]
                    ] )
                checkoutstr = 'checkout' if checkout else 'checkin'
                status_url = self.urlStatus+'/dibs/'+checkoutstr
                request = urllib.request.Request(url = status_url, data = argsdata, headers = headers, method = "POST")
                log(f'headers {request.headers}')
                log(f'checkout item url is {status_url}')
                connection = urllib.request.urlopen(request)
                log(f'status = {connection.status}')
                return (True)
        except HTTPError as ex:
            log(f'Error performing {checkoutstr} for {barcode} in Sirsi')
            log(f'status is {ex.status}')
            log(f'message is {ex.msg}')
            raise ValueError(f'{ex.status} {ex.msg} performing {checkoutstr} for {barcode} in Sirsi'  )
        except URLError as ex:
            log(f'Error performing {checkoutstr} for {barcode} in Sirsi')
            log(f'message is {ex.reason.strerror}')
            raise ValueError(f'{ex.reason.strerror} performing {checkoutstr} for {barcode} in Sirsi'  )
        except Exception as ex:
            exceptionMessage = repr(ex)
            log(f'exceptionMessage {exceptionMessage}')
            raise ex

    def getGuestAuthKey(self):
            ''' get authorization key '''
            if (self.secret != None):
                expirationTime = int((datetime.now() + timedelta(minutes=20)).timestamp())
                values =  {'userId': 'anonymous', 'isUva': False, 'homeLibrary': '', 'profile': '', 'canPurchase': False, 'canLEO': False, 'canLEOPlus': False, 'canPlaceReserve': False, 'useSIS': False, 'role': 'guest', 'authMethod': 'none', 'exp': expirationTime, 'iss': 'v4'}
                log(f'Getting authorization key from {self.urlAuth}')
                data = urllib.parse.urlencode(values).encode("utf-8")
                log(f'Building authorization key using jwt encode')
                self.authKey = jwt.encode(values, self.secret, algorithm="HS256")
                log(f'authKey = {self.authKey}')
            elif (self.urlAuth != None) :
                authConnection = urllib.request.urlopen(url=self.urlAuth, data=data)
                status = authConnection.status
                log(f'status = {status}')
                authKeyBytes = authConnection.read()
                self.authKey = str(authKeyBytes, "utf-8")
                log(f'authKey = {self.authKey}')
            else :
                self.authKey = None

    def getAuthKeyForPerson(self, username = None):
            ''' build authorization key '''
            if (username != None and self.secret != None):
                expirationTime = int((datetime.now() + timedelta(minutes=20)).timestamp())
                values = {"iss" : "v4", "userId" : f'{username}', "exp" : expirationTime}
                log(f'Building authorization key for user {username} using jwt encode')
                log(f'Using secret key {self.secret}')
                self.authKey = jwt.encode(values, self.secret, algorithm="HS256")
                log(f'authKey = {self.authKey}')
            else :
                self.authKey = None


class FolioInterface(LSPInterface):
    '''Interface layer for FOLIO hosted LSP servers.'''

    def __init__(self, url = None, token = None, tenant_id = None,
                 an_prefix = None, page_template = None, thumbnails_dir = None):
        '''Create an interface for the server at "url".'''
        self.url = url
        self._token = token
        self._tenant_id = tenant_id
        self._an_prefix = an_prefix
        self._page_tmpl = page_template
        self._thumbnails_dir = thumbnails_dir
        self._folio = Folio(okapi_url     = url,
                            okapi_token   = token,
                            tenant_id     = tenant_id,
                            an_prefix     = an_prefix)


    @property
    def name(self):
        '''Return the name of this LSP, for use in (e.g.) error messages.'''
        return 'FOLIO'


    def record(self, barcode = None):
        '''Return a record for the item identified by the "barcode".

        This will return None if no such entry can be found in FOLIO.
        It will raise a ValueError exception if an entry is found but lacks
        the 3 most basic metadata fields of title, author and year.
        '''
        try:
            rec = self._folio.record(barcode = barcode)
        except pokapi.exceptions.NotFound:
            log(f'could not find {barcode} in FOLIO')
            return None

        log(f'record for {barcode} has id {rec.id}')
        if not all([rec.title, rec.author, rec.year]):
            log(f'record for {barcode} in FOLIO lacks minimum metadata')
            raise ValueError('Got incomplete record for {barcode} in {self.url}')

        thumbnail_file = join(self._thumbnails_dir, barcode + '.jpg')
        if not exists(thumbnail_file):
            if rec.isbn_issn:
                try:
                    save_thumbnail(thumbnail_file, isbn = rec.isbn_issn)
                except Exception as ex:  # noqa PIE786
                    # Log it and go on; don't fail just because of this.
                    log(f'failed to save thumbnail for {barcode}: ' + str(ex))
            else:
                log(f"{rec.id} has no ISBN/ISSN => can't get a thumbnail")
        else:
            log(f'thumbnail image already exists in {thumbnail_file}')

        page = self._page_tmpl.format(accession_number = rec.accession_number)
        return LSPRecord(item_id   = rec.id,
                         item_page = page,
                         title     = truncated_title(rec.title),
                         author    = rec.author,
                         year      = rec.year,
                         publisher = rec.publisher or '',
                         edition   = rec.edition or '',
                         isbn_issn = rec.isbn_issn or '')


class UnconfiguredInterface(LSPInterface):
    '''Dummy interface, for when no LSP is chosen.'''

    def __repr__(self):
        '''Return a string representing this interface object.'''
        return "<{}>".format(self.__class__.__name__)


    def record(self, barcode = None):
        '''Return a record for the item identified by the "barcode".'''
        return LSPRecord(item_id   = 'LSP not configured',
                         item_page = '',
                         title     = 'LSP not configured',
                         author    = 'LSP not configured',
                         publisher = 'LSP not configured',
                         year      = 'LSP not configured',
                         edition   = 'LSP not configured',
                         isbn_issn = '')



# Primary exported class.
# .............................................................................

class LSP(LSPInterface):
    '''LSP abstraction class.'''

    def __new__(cls, *args, **kwds):
        # This implements a Singleton pattern by storing the object we create
        # and returning the same one if the class constructor is called again.
        lsp = cls.__dict__.get("__lsp_interface__")
        if lsp is not None:
            log(f'Using previously-created LSP object {str(cls)}')
            return lsp

        # Read common configuration variables.
        thumbnails_dir = resolved_path(config('THUMBNAILS_DIR', section = 'dibs'))
        log(f'assuming thumbnails dir is {thumbnails_dir}')

        # Select the appropriate interface type and create the object.
        lsp_type = config('LSP_TYPE').lower()
        if lsp_type == 'folio':
            def folio_config(key):
                return config(key, section = 'folio')

            url           = folio_config('FOLIO_OKAPI_URL')
            token         = folio_config('FOLIO_OKAPI_TOKEN')
            tenant_id     = folio_config('FOLIO_OKAPI_TENANT_ID')
            an_prefix     = folio_config('FOLIO_ACCESSION_PREFIX')
            page_template = folio_config('EDS_PAGE_TEMPLATE')
            log(f'Using FOLIO URL {url} with tenant id {tenant_id}')
            lsp = FolioInterface(url = url,
                                 token = token,
                                 tenant_id = tenant_id,
                                 an_prefix = an_prefix,
                                 page_template = page_template,
                                 thumbnails_dir = thumbnails_dir)
        elif lsp_type == 'tind':
            url = config('TIND_SERVER_URL', section = 'tind')
            log(f'Using TIND URL {url}')
            lsp = TindInterface(url, thumbnails_dir = thumbnails_dir)
        elif lsp_type == 'solr':
            url = config('SOLR_SERVER_URL', section = 'solr')
            lsp = SolrInterface(url)
        elif lsp_type == 'poolapi':
            url = config('POOL_URL', section = 'poolapi')
            urlAuth = config('AUTH_URL', section = 'poolapi')
            urlStatus = config('STATUS_URL', default = None, section = 'poolapi')
            secret = config('JWT_KEY', default = "nokeynohow", section = 'poolapi')
            lsp = VirgoAPIInterface(url, urlAuth, urlStatus, secret)
        else:
            lsp = UnconfiguredInterface()

        # Store the interface object (to implement the Singleton pattern).
        cls.__lsp_interface__ = lsp
        return lsp


# Internal utilities.
# .............................................................................

def save_thumbnail(dest_file, url = None, isbn = None):
    image = None
    cc_user = config('CC_USER', section = 'contentcafe', default = None)
    cc_password = config('CC_PASSWORD', section = 'contentcafe', default = None)
    cc_login = (cc_user, cc_password) if (cc_user and cc_password) else None

    if isbn:
        url, image = cover_image(isbn, size = 'L', cc_login = cc_login)
        log(f'cover_image returned image at {url}')
    # We were either given a url in the call, or we found one using the isbn.
    elif url:
        (response, error) = net('get', url)
        if not error and response.status_code == 200:
            log(f'got image from {url}')
            image = response.content
    if image:
        log(f'will save cover image in {dest_file}')
        with open(dest_file, 'wb') as file:
            file.write(image)
    else:
        log(f'no cover image found for {url}')


def probable_issn(value):
    return len(value) < 10 and '-' in value


def truncated_title(title):
    modified_title = re.split(r':|;|\.', title)[0].strip()
    if len(modified_title) > 60:
        return wrap(modified_title, 60)[0] + ' ...'
    else:
        return modified_title
