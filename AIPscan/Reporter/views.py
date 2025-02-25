# -*- coding: utf-8 -*-

"""Views contains the primary routes for navigation around AIPscan's
Reporter module. Reports themselves as siphoned off into separate module
files with singular responsibility for a report.
"""

from datetime import datetime

from flask import jsonify, make_response, render_template, request, session

from AIPscan.models import (
    AIP,
    Event,
    FetchJob,
    File,
    FileType,
    Pipeline,
    StorageLocation,
    StorageService,
)

# Flask's idiom requires code using routing decorators to be imported
# up-front. But that means it might not be called directly by a module.
from AIPscan.Reporter import (  # noqa: F401
    report_aip_contents,
    report_aips_by_format,
    report_aips_by_puid,
    report_format_versions_count,
    report_formats_count,
    report_ingest_log,
    report_largest_aips,
    report_largest_files,
    report_preservation_derivatives,
    report_storage_locations,
    reporter,
    request_params,
    sort_puids,
)


def _get_storage_service(storage_service_id):
    """Get Storage Service from specified ID.

    If the requested Storage Service ID is invalid, return (in order of
    preference) one of the following:
    - First default Storage Service
    - First Storage Service
    - None

    :param storage_service_id: Storage Service ID

    :returns: StorageService object or None
    """
    storage_service = StorageService.query.get(storage_service_id)
    if storage_service is None:
        storage_service = StorageService.query.filter_by(default=True).first()
    if storage_service is None:
        storage_service = StorageService.query.first()
    return storage_service


def _get_storage_location(storage_location_id):
    """Return Storage Location or None."""
    return StorageLocation.query.get(storage_location_id)


def storage_locations_with_aips(storage_locations):
    """Return list of Storage Locations filtered to those with AIPs."""
    return [loc for loc in storage_locations if loc.aips]


@reporter.route("/aips/", methods=["GET"])
def view_aips():
    """Overview of AIPs in given Storage Service and Location."""
    storage_service_id = request.args.get(request_params.STORAGE_SERVICE_ID)
    storage_service = _get_storage_service(storage_service_id)

    storage_location_id = request.args.get(request_params.STORAGE_LOCATION_ID)
    try:
        storage_location = _get_storage_location(storage_location_id)
    except Exception as e:
        print(e)

    aips = AIP.query.filter_by(storage_service_id=storage_service.id)
    if storage_location:
        aips = aips.filter_by(storage_location_id=storage_location_id)
    aips = aips.all()

    return render_template(
        "aips.html",
        storage_services=StorageService.query.all(),
        storage_service=storage_service,
        storage_locations=storage_locations_with_aips(
            storage_service.storage_locations
        ),
        storage_location=storage_location,
        aips=aips,
    )


# Picturae TODO: Does this work with AIP UUID as well?
@reporter.route("/aip/<aip_id>", methods=["GET"])
def view_aip(aip_id):
    """Detailed view of specific AIP."""
    aip = AIP.query.get(aip_id)
    fetch_job = FetchJob.query.get(aip.fetch_job_id)
    storage_service = StorageService.query.get(fetch_job.storage_service_id)
    storage_location = StorageLocation.query.get(aip.storage_location_id)
    aips_count = AIP.query.filter_by(storage_service_id=storage_service.id).count()
    original_file_count = aip.original_file_count
    preservation_file_count = aip.preservation_file_count
    originals = []
    original_files = File.query.filter_by(
        aip_id=aip.id, file_type=FileType.original
    ).all()
    origin_pipeline = Pipeline.query.get(aip.origin_pipeline_id)
    for file_ in original_files:
        original = {}
        original["id"] = file_.id
        original["name"] = file_.name
        original["uuid"] = file_.uuid
        original["size"] = file_.size
        original["date_created"] = file_.date_created.strftime("%Y-%m-%d")
        original["puid"] = file_.puid
        original["file_format"] = file_.file_format
        original["format_version"] = file_.format_version
        preservation_file = File.query.filter_by(
            file_type=FileType.preservation, original_file_id=file_.id
        ).first()
        if preservation_file is not None:
            original["preservation_file_id"] = preservation_file.id
        originals.append(original)

    return render_template(
        "aip.html",
        aip=aip,
        storage_service=storage_service,
        storage_location=storage_location,
        aips_count=aips_count,
        originals=originals,
        original_file_count=original_file_count,
        preservation_file_count=preservation_file_count,
        origin_pipeline=origin_pipeline,
    )


@reporter.route("/file/<file_id>", methods=["GET"])
def view_file(file_id):
    """File page displays Object and Event metadata for file"""
    file_ = File.query.get(file_id)
    aip = AIP.query.get(file_.aip_id)
    events = Event.query.filter_by(file_id=file_id).all()
    preservation_file = File.query.filter_by(
        file_type=FileType.preservation, original_file_id=file_.id
    ).first()

    original_filename = None
    if file_.original_file_id is not None:
        original_file = File.query.get(file_.original_file_id)
        original_filename = original_file.name

    return render_template(
        "file.html",
        file_=file_,
        aip=aip,
        events=events,
        preservation_file=preservation_file,
        original_filename=original_filename,
    )


@reporter.route("/reports/", methods=["GET"])
def reports():
    """Reports page lists available built-in reports

    Storage Service ID can be specified as an optional parameter. If
    one is not specified, use the default Storage Service.
    """
    storage_service_id = request.args.get(request_params.STORAGE_SERVICE_ID)
    storage_service = _get_storage_service(storage_service_id)

    storage_location_id = request.args.get(request_params.STORAGE_LOCATION_ID)
    storage_location = _get_storage_location(storage_location_id)

    original_file_formats = []
    preservation_file_formats = []
    original_puids = []
    preservation_puids = []

    # Filter dropdowns by Storage Location if one is selected. If a location is
    # not selected, populate dropdowns from Storage Service instead.
    if storage_location:
        # Original file formats and PUIDs should be present for any Storage
        # Loocation with ingested files.
        try:
            original_file_formats = storage_location.unique_original_file_formats
            original_puids = sort_puids(storage_location.unique_original_puids)
        except AttributeError:
            pass

        # Preservation file formats and PUIDs may be present depending on
        # a number of factors such as processing configuration choices,
        # normalization rules, and use of manual normalization.
        try:
            preservation_file_formats = (
                storage_location.unique_preservation_file_formats
            )
        except AttributeError:
            pass
        try:
            preservation_puids = sort_puids(storage_location.unique_preservation_puids)
        except AttributeError:
            pass

    else:
        # Original file formats and PUIDs should be present for any Storage
        # Service with ingested files.
        try:
            original_file_formats = storage_service.unique_original_file_formats
            original_puids = sort_puids(storage_service.unique_original_puids)
        except AttributeError:
            pass

        # Preservation file formats and PUIDs may be present depending on
        # a number of factors such as processing configuration choices,
        # normalization rules, and use of manual normalization.
        try:
            preservation_file_formats = storage_service.unique_preservation_file_formats
        except AttributeError:
            pass
        try:
            preservation_puids = sort_puids(storage_service.unique_preservation_puids)
        except AttributeError:
            pass

    if "start_date" not in session:
        earliest_aip_created = storage_service.earliest_aip_created
        session["start_date"] = earliest_aip_created.strftime("%Y-%m-%d")

    if "end_date" not in session:
        now = datetime.now()
        session["end_date"] = str(datetime(now.year, now.month, now.day))[:-9]

    return render_template(
        "reports.html",
        storage_service=storage_service,
        storage_services=StorageService.query.all(),
        storage_location=storage_location,
        storage_locations=storage_locations_with_aips(
            storage_service.storage_locations
        ),
        original_file_formats=original_file_formats,
        preservation_file_formats=preservation_file_formats,
        original_puids=original_puids,
        preservation_puids=preservation_puids,
        start_date=session["start_date"],
        end_date=session["end_date"],
    )


@reporter.route("/update_dates/", methods=["POST"])
def update_dates():
    if request.json and request.json.get("start_date"):
        req = request.get_json()
        session["start_date"] = request.json.get("start_date")
        return make_response(jsonify(req), 200)

    if request.json and request.json.get("end_date"):
        req = request.get_json()
        session["end_date"] = request.json.get("end_date")
        return make_response(jsonify(req), 200)
