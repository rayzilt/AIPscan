import json
import os
from datetime import datetime

import pytest

from AIPscan import test_helpers
from AIPscan.Aggregator.tasks import (
    TaskError,
    get_mets,
    make_request,
    parse_packages_and_load_mets,
)
from AIPscan.Aggregator.tests import (
    INVALID_JSON,
    REQUEST_URL,
    REQUEST_URL_WITHOUT_API_KEY,
    RESPONSE_DICT,
    VALID_JSON,
    MockResponse,
)
from AIPscan.models import AIP

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
FIXTURES_DIR = os.path.join(SCRIPT_DIR, "fixtures")


def _get_aips(storage_service_id):
    """Return queryset of AIPs associated with Storage Service ID."""
    return AIP.query.filter_by(storage_service_id=storage_service_id).all()


@pytest.mark.parametrize(
    "fixture_path, package_uuid",
    [
        # First METS file.
        (
            os.path.join("features_mets", "features-mets.xml"),
            "ab793f82-27b0-4c2e-ac3e-621bab5af8f1",
        ),
        # Another METS file.
        (
            os.path.join("images_mets", "images.xml"),
            "2d718ecf-828a-4487-83ce-873cf9edca1a",
        ),
    ],
)
def test_get_mets_task(app_instance, tmpdir, mocker, fixture_path, package_uuid):
    """Test that fetch jobs after the first don't duplicate content."""
    mets_file = os.path.join(FIXTURES_DIR, fixture_path)

    def mock_download_mets(
        api_url, package_uuid, relative_path_to_mets, timestamp_str, package_list_no
    ):
        return mets_file

    mocker.patch("AIPscan.Aggregator.tasks.download_mets", mock_download_mets)
    delete_mets_file = mocker.patch("AIPscan.Aggregator.tasks.os.remove")

    storage_service = test_helpers.create_test_storage_service()
    storage_location = test_helpers.create_test_storage_location(
        storage_service_id=storage_service.id
    )
    pipeline = test_helpers.create_test_pipeline(storage_service_id=storage_service.id)

    get_storage_location = mocker.patch(
        "AIPscan.Aggregator.database_helpers.create_or_update_storage_location"
    )
    get_storage_location.return_value = storage_location

    # No AIPs should exist at this point.
    aips = _get_aips(storage_service.id)
    assert not aips

    api_url = {"baseUrl": "http://test-url", "userName": "test", "apiKey": "test"}

    # Create AIP and verify record.
    fetch_job1 = test_helpers.create_test_fetch_job(
        storage_service_id=storage_service.id
    )
    get_mets(
        package_uuid=package_uuid,
        aip_size=1000,
        relative_path_to_mets="test",
        api_url=api_url,
        timestamp_str=datetime.now()
        .replace(microsecond=0)
        .strftime("%Y-%m-%d-%H-%M-%S"),
        package_list_no=1,
        storage_service_id=storage_service.id,
        storage_location_id=storage_location.id,
        fetch_job_id=fetch_job1.id,
        origin_pipeline_id=pipeline.id,
    )
    aips = _get_aips(storage_service.id)
    assert len(aips) == 1
    assert len(fetch_job1.aips) == 1

    original_mets_sha256 = aips[0].mets_sha256

    # Try to create AIP again and verify no duplicate is created.
    fetch_job2 = test_helpers.create_test_fetch_job(
        storage_service_id=storage_service.id
    )
    get_mets(
        package_uuid=package_uuid,
        aip_size=1000,
        relative_path_to_mets="test",
        api_url=api_url,
        timestamp_str=datetime.now()
        .replace(microsecond=0)
        .strftime("%Y-%m-%d-%H-%M-%S"),
        package_list_no=1,
        storage_service_id=storage_service.id,
        storage_location_id=storage_location.id,
        fetch_job_id=fetch_job2.id,
        origin_pipeline_id=pipeline.id,
    )
    aips = _get_aips(storage_service.id)
    assert len(aips) == 1
    assert aips[0].mets_sha256 == original_mets_sha256
    assert len(fetch_job1.aips) == 1
    assert len(fetch_job2.aips) == 0

    # Replace METS with a new METS file and run again. The old AIP record
    # should be deleted and replaced with one from the new METS.
    mets_file = os.path.join(FIXTURES_DIR, "iso_mets", "iso_mets.xml")
    fetch_job3 = test_helpers.create_test_fetch_job(
        storage_service_id=storage_service.id
    )
    get_mets(
        package_uuid=package_uuid,
        aip_size=1000,
        relative_path_to_mets="test",
        api_url=api_url,
        timestamp_str=datetime.now()
        .replace(microsecond=0)
        .strftime("%Y-%m-%d-%H-%M-%S"),
        package_list_no=1,
        storage_service_id=storage_service.id,
        storage_location_id=storage_location.id,
        fetch_job_id=fetch_job3.id,
        origin_pipeline_id=pipeline.id,
    )
    aips = _get_aips(storage_service.id)
    assert len(aips) == 1
    assert aips[0].mets_sha256 != original_mets_sha256
    assert len(fetch_job1.aips) == 0
    assert len(fetch_job2.aips) == 0
    assert len(fetch_job3.aips) == 1

    delete_calls = [
        mocker.call(os.path.join(FIXTURES_DIR, fixture_path)),
        mocker.call(mets_file),
    ]
    delete_mets_file.assert_has_calls(delete_calls, any_order=True)
    delete_mets_file.call_count == 3


@pytest.mark.parametrize(
    "response, raises_task_error",
    [
        # Test 200 response with valid JSON.
        (MockResponse(200, VALID_JSON), False),
        # Test 500 response raises TaskError.
        (MockResponse(500, VALID_JSON), True),
        # Test 200 response with invalid JSON raises TaskError.
        (MockResponse(200, INVALID_JSON), True),
    ],
)
def test_make_request(mocker, response, raises_task_error):
    """Test handling of Storage Service response."""
    request = mocker.patch("AIPscan.Aggregator.tasks.requests.get")
    request.return_value = response

    if raises_task_error:
        with pytest.raises(TaskError):
            _ = make_request(REQUEST_URL, REQUEST_URL_WITHOUT_API_KEY)
    else:
        return_dict = make_request(REQUEST_URL, REQUEST_URL_WITHOUT_API_KEY)
        assert return_dict["key"] == RESPONSE_DICT["key"]


def test_parse_packages_and_load_mets(app_instance, tmpdir, mocker):
    """Test that JSON package lists are deleted after being parsed."""
    json_file_path = tmpdir.join("packages.json")
    json_file_path.write(json.dumps({"objects": []}))

    delete_package_json = mocker.patch("AIPscan.Aggregator.tasks.os.remove")

    parse_packages_and_load_mets(json_file_path, {}, str(datetime.now()), 1, 1, 1)

    delete_package_json.assert_called_with(json_file_path)
