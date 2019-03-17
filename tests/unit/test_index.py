import sys
import unittest

import responses

from intezer_sdk import consts
from intezer_sdk import errors
from intezer_sdk.api import set_global_api
from intezer_sdk.index import Index

try:
    from unittest.mock import mock_open
    from unittest.mock import patch
except ImportError:
    from mock import mock_open
    from mock import patch


class IndexSpec(unittest.TestCase):
    def setUp(self):
        self.full_url = consts.BASE_URL + consts.API_VERSION
        consts.CHECK_STATUS_INTERVAL = 0

        # Python 2 support
        if sys.version_info[0] < 3:
            self.patch_prop = '__builtin__.open'
        else:
            self.patch_prop = 'builtins.open'

        set_global_api()

    def test_index_malicious_without_family_name_raise_value_error(self):
        # Act + Assert
        with self.assertRaises(ValueError):
            Index(sha256='a', index_as=consts.IndexType.MALICIOUS)

    def test_trusted_index_by_sha256_status_change_to_created(self):
        # Arrange
        with responses.RequestsMock() as mock:
            mock.add('POST',
                     url=self.full_url + '/get-access-token',
                     status=200,
                     json={'result': 'accesstoken'})
            mock.add('POST',
                     url=self.full_url + '/files/{}/index'.format('a'),
                     status=201,
                     json={'result_url': '/files/index/testindex'})
            index = Index(sha256='a', index_as=consts.IndexType.TRUSTED)

            # Act
            index.send()

        # Assert
        self.assertEqual(index.status, consts.IndexStatusCode.CREATED)

    def test_failed_index_raise_index_failed(self):
        # Arrange
        with responses.RequestsMock() as mock:
            mock.add('POST',
                     url=self.full_url + '/get-access-token',
                     status=200,
                     json={'result': 'accesstoken'})
            mock.add('POST',
                     url=self.full_url + '/files/{}/index'.format('a'),
                     status=201,
                     json={'result_url': '/files/index/testindex'})
            mock.add('GET',
                     url=self.full_url + '/files/index/testindex',
                     status=200,
                     json={'result_url': '/files/index/testindex',
                           'status': 'failed'})
            index = Index(sha256='a', index_as=consts.IndexType.TRUSTED)

            # Act + Assert
            with self.assertRaises(errors.IndexFailed):
                index.send(wait=True)

    def test_malicious_index_by_sha256_status_change_to_created(self):
        # Arrange
        with responses.RequestsMock() as mock:
            mock.add('POST',
                     url=self.full_url + '/get-access-token',
                     status=200,
                     json={'result': 'accesstoken'})
            mock.add('POST',
                     url=self.full_url + '/files/{}/index'.format('a'),
                     status=201,
                     json={'result_url': '/files/index/testindex'})
            index = Index(sha256='a', index_as=consts.IndexType.MALICIOUS, family_name='WannaCry')

            # Act
            index.send()

        # Assert
        self.assertEqual(index.status, consts.IndexStatusCode.CREATED)

    def test_index_by_sha256_raise_sha256_do_not_exist(self):
        # Arrange
        with responses.RequestsMock() as mock:
            mock.add('POST',
                     url=self.full_url + '/get-access-token',
                     status=200,
                     json={'result': 'accesstoken'})
            mock.add('POST',
                     url=self.full_url + '/files/{}/index'.format('a'),
                     status=404)
            index = Index(sha256='a', index_as=consts.IndexType.TRUSTED)

            # Act + Assert
            with self.assertRaises(errors.HashDoesNotExistError):
                index.send(wait=True)

    def test_index_by_file_status_change(self):
        # Arrange
        with responses.RequestsMock() as mock:
            mock.add('POST',
                     url=self.full_url + '/get-access-token',
                     status=200,
                     json={'result': 'accesstoken'})
            mock.add('POST',
                     url=self.full_url + '/files/index',
                     status=201,
                     json={'result_url': '/files/index/testindex'})
            index = Index(file_path='a', index_as=consts.IndexType.TRUSTED)

            with patch(self.patch_prop, mock_open(read_data='data')):
                # Act
                index.send()

        # Assert
        self.assertEqual(index.status, consts.IndexStatusCode.CREATED)

    def test_index_by_sha256_status_finish(self):
        # Arrange
        with responses.RequestsMock() as mock:
            mock.add('POST',
                     url=self.full_url + '/get-access-token',
                     status=200,
                     json={'result': 'accesstoken'})
            mock.add('POST',
                     url=self.full_url + '/files/{}/index'.format('a'),
                     status=201,
                     json={'result_url': '/files/index/testindex'})
            mock.add('GET',
                     url=self.full_url + '/files/index/testindex',
                     status=202)
            mock.add('GET',
                     url=self.full_url + '/files/index/testindex',
                     status=202)
            mock.add('GET',
                     url=self.full_url + '/files/index/testindex',
                     status=200,
                     json={'result_url': '/files/index/testindex',
                           'status': 'succeeded'})
            index = Index(sha256='a', index_as=consts.IndexType.TRUSTED)

            # Act
            index.send(wait=True)

        # Assert
        self.assertEqual(index.status, consts.IndexStatusCode.FINISH)

    def test_index_by_file_succeeded_status_changed_to_finish(self):
        # Arrange
        with responses.RequestsMock() as mock:
            mock.add('POST',
                     url=self.full_url + '/get-access-token',
                     status=200,
                     json={'result': 'accesstoken'})
            mock.add('POST',
                     url=self.full_url + '/files/index',
                     status=201,
                     json={'result_url': '/files/index/testindex'})
            mock.add('GET',
                     url=self.full_url + '/files/index/testindex',
                     status=202)
            mock.add('GET',
                     url=self.full_url + '/files/index/testindex',
                     status=202)
            mock.add('GET',
                     url=self.full_url + '/files/index/testindex',
                     status=200,
                     json={'result_url': '/files/index/testindex',
                           'status': 'succeeded'})
            index = Index(file_path='a', index_as=consts.IndexType.TRUSTED)

            with patch(self.patch_prop, mock_open(read_data='data')):
                # Act
                index.send(wait=True)

        # Assert
        self.assertEqual(index.status, consts.IndexStatusCode.FINISH)

    def test_check_status_before_index_sent_raise_status(self):
        # Arrange
        index = Index(sha256='a', index_as=consts.IndexType.TRUSTED)

        # Act + Assert
        with self.assertRaises(errors.IntezerError):
            index.check_status()

    def test_send_index_by_file_with_pulling_and_get_status_finish(self):
        # Arrange
        with responses.RequestsMock() as mock:
            mock.add('POST',
                     url=self.full_url + '/get-access-token',
                     status=200,
                     json={'result': 'accesstoken'})
            mock.add('POST',
                     url=self.full_url + '/files/index',
                     status=201,
                     json={'result_url': '/files/index/testindex'})
            mock.add('GET',
                     url=self.full_url + '/files/index/testindex',
                     status=202)
            mock.add('GET',
                     url=self.full_url + '/files/index/testindex',
                     status=202)
            mock.add('GET',
                     url=self.full_url + '/files/index/testindex',
                     status=200,
                     json={'result_url': '/files/index/testindex',
                           'status': 'succeeded'})
            index = Index(file_path='a', index_as=consts.IndexType.TRUSTED)

            with patch(self.patch_prop, mock_open(read_data='data')):
                # Act
                index.send()
                index.check_status()
                index.check_status()
                index.check_status()

        # Assert
        self.assertEqual(index.status, consts.IndexStatusCode.FINISH)

    def test_parallel_index_by_sha256_succeeded_status_changed_to_finish(self):
        # Arrange
        with responses.RequestsMock() as mock:
            first_index_name = 'a'
            second_index_name = 'b'
            mock.add('POST',
                     url=self.full_url + '/get-access-token',
                     status=200,
                     json={'result': 'accesstoken'})
            mock.add('POST',
                     url=self.full_url + '/files/{}/index'.format(first_index_name),
                     status=201,
                     json={'result_url': '/files/index/first'})
            mock.add('POST',
                     url=self.full_url + '/files/{}/index'.format(second_index_name),
                     status=201,
                     json={'result_url': '/files/index/second'})
            mock.add('GET',
                     url=self.full_url + '/files/index/first',
                     status=200,
                     json={'result_url': '/files/index/testindex',
                           'status': 'succeeded'})
            mock.add('GET',
                     url=self.full_url + '/files/index/second',
                     status=200,
                     json={'result_url': '/files/index/testindex',
                           'status': 'succeeded'})
            first_index = Index(sha256=first_index_name, index_as=consts.IndexType.TRUSTED)
            second_index = Index(sha256=second_index_name, index_as=consts.IndexType.TRUSTED)

            # Act
            first_index.send()
            second_index.send()
            first_index.wait_for_completion()
            second_index.wait_for_completion()

        # Assert
        self.assertEqual(first_index.status, consts.IndexStatusCode.FINISH)
        self.assertEqual(second_index.status, consts.IndexStatusCode.FINISH)
