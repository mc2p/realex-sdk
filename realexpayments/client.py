from logging import getLogger
from xml.etree.ElementTree import fromstring
from .exceptions import RealexError, RealexServerError
from .utils import HttpUtils, ResponseUtils


logger = getLogger(__name__)


class RealexClient(object):
    def __init__(self, secret, timeout=65, only_allow_https=True, proxies=None):
        self.secret = secret
        self.timeout = timeout
        self.only_allow_https = only_allow_https
        self.proxies = proxies

    def send(self, url, request):
        logger.info('Sending XML request to Realex.')

        # generate any required defaults e.g. order ID, time stamp, hash
        request.generate_defaults(self.secret)

        # convert request to XML
        logger.debug('Marshalling request object to XML.')
        request_xml = request.to_xml()

        # log the request
        logger.info('Request XML to server: %s' % request_xml)

        response_xml = HttpUtils.send(url, request_xml, self.timeout, self.only_allow_https, self.proxies)

        # log the response
        logger.info('Response XML from server: %s' % response_xml)

        logger.debug('Unmarshalling XML to response object.')
        response = request.response_from_xml(fromstring(response_xml))

        if ResponseUtils.is_basic_response(response.result):
            logger.error('Error response received from Realex with code %s and message %s.' %
                         (response.result, response.message))
            raise RealexServerError(response.timestamp, response.order_id, response.result, response.message)

        if not response.is_hash_valid(self.secret):
            logger.error('Response hash is invalid. This response\'s validity cannot be verified.')
            raise RealexError('Response hash is invalid. This response\'s validity cannot be verified.')

        return response