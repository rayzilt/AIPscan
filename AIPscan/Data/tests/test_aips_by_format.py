# -*- coding: utf-8 -*-

import pytest

from AIPscan.Data import fields, report_data
from AIPscan.Data.tests import (
    MOCK_AIPS_BY_FORMAT_OR_PUID_QUERY_RESULTS as MOCK_QUERY_RESULTS,
)
from AIPscan.Data.tests import (
    MOCK_STORAGE_SERVICE,
    MOCK_STORAGE_SERVICE_ID,
    MOCK_STORAGE_SERVICE_NAME,
)
from AIPscan.Data.tests.conftest import (
    ORIGINAL_FILE_SIZE,
    PRESERVATION_FILE_SIZE,
    TIFF_FILE_FORMAT,
)


@pytest.mark.parametrize(
    "query_results, results_count",
    [
        # Empty result set, count is 0.
        ([], 0),
        # Test the return of complete result set, count is the length
        # of all results.
        (MOCK_QUERY_RESULTS, len(MOCK_QUERY_RESULTS)),
        # Test the return of only the first two results, count is 2.
        (MOCK_QUERY_RESULTS[:2], 2),
    ],
)
def test_aips_by_file_format(app_instance, mocker, query_results, results_count):
    """Test that results match high-level expectations."""
    mock_query = mocker.patch(
        "AIPscan.Data.report_data._query_aips_by_file_format_or_puid"
    )
    mock_query.return_value = query_results

    mock_get_ss = mocker.patch("AIPscan.Data.report_data._get_storage_service")
    mock_get_ss.return_value = MOCK_STORAGE_SERVICE

    report = report_data.aips_by_file_format(
        MOCK_STORAGE_SERVICE_ID, "Some file format"
    )
    assert report[fields.FIELD_STORAGE_NAME] == MOCK_STORAGE_SERVICE_NAME
    assert len(report[fields.FIELD_AIPS]) == results_count


@pytest.mark.parametrize(
    "test_aip", [mock_result for mock_result in MOCK_QUERY_RESULTS]
)
def test_aips_by_file_format_aip_elements(app_instance, mocker, test_aip):
    """Test that structure of AIP data matches expectations."""
    mock_query = mocker.patch(
        "AIPscan.Data.report_data._query_aips_by_file_format_or_puid"
    )
    mock_query.return_value = [test_aip]

    mock_get_ss = mocker.patch("AIPscan.Data.report_data._get_storage_service")
    mock_get_ss.return_value = MOCK_STORAGE_SERVICE

    report = report_data.aips_by_file_format(
        MOCK_STORAGE_SERVICE_ID, "Some file format"
    )
    report_aip = report[fields.FIELD_AIPS][0]

    assert test_aip.id == report_aip.get(fields.FIELD_ID)
    assert test_aip.name == report_aip.get(fields.FIELD_AIP_NAME)
    assert test_aip.uuid == report_aip.get(fields.FIELD_UUID)
    assert test_aip.file_count == report_aip.get(fields.FIELD_COUNT)
    assert test_aip.total_size == report_aip.get(fields.FIELD_SIZE)


@pytest.mark.parametrize(
    "format_name, original_files, aip_count, total_file_count, total_file_size",
    [
        # Original format in test data should be included in results.
        (TIFF_FILE_FORMAT, True, 1, 1, ORIGINAL_FILE_SIZE),
        # Original format not in test data should not be included in
        # results.
        ("Maya Binary", True, 0, 0, 0),
        # Preservation format in test data should be included in
        # results.
        (TIFF_FILE_FORMAT, False, 1, 1, PRESERVATION_FILE_SIZE),
        # Non-existent preservation format not present in test data
        # should not be included in results.
        ("PDF/Z", False, 0, 0, 0),
        # Passing a None value for original_files returns original
        # files.
        (TIFF_FILE_FORMAT, None, 1, 1, ORIGINAL_FILE_SIZE),
        # Passing an incorrect value for original_files returns
        # original files.
        (TIFF_FILE_FORMAT, "invalid", 1, 1, ORIGINAL_FILE_SIZE),
    ],
)
def test_aips_by_file_format_contents(
    app_with_populated_files,
    format_name,
    original_files,
    aip_count,
    total_file_count,
    total_file_size,
):
    """Test that content of response matches expectations.

    This integration test uses a pre-populated fixture to verify that
    the database access layer of our endpoint returns what we expect.
    """
    results = report_data.aips_by_file_format(
        storage_service_id=1, file_format=format_name, original_files=original_files
    )
    aips = results[fields.FIELD_AIPS]
    assert len(aips) == aip_count
    assert sum(aip[fields.FIELD_COUNT] for aip in aips) == total_file_count
    assert sum(aip[fields.FIELD_SIZE] for aip in aips) == total_file_size
