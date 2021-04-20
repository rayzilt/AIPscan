# -*- coding: utf-8 -*-

"""Report formats count consists of the tabular report, plot, and
chart which describe the file formats present across the AIPs in a
storage service with AIPs filtered by date range.
"""

from collections import Counter
from datetime import datetime, timedelta

from flask import render_template, request

from AIPscan.Data import fields, report_data
from AIPscan.helpers import filesizeformat, parse_bool, parse_datetime_bound
from AIPscan.models import AIP, File, FileType, StorageService
from AIPscan.Reporter import (
    download_csv,
    get_display_end_date,
    reporter,
    request_params,
    translate_headers,
)

HEADERS = [fields.FIELD_FORMAT, fields.FIELD_COUNT, fields.FIELD_SIZE]


@reporter.route("/report_formats_count/", methods=["GET"])
def report_formats_count():
    """Report (tabular) on all file formats and their counts and size on
    disk across all AIPs in the storage service.
    """
    storage_service_id = request.args.get(request_params.STORAGE_SERVICE_ID)
    start_date = parse_datetime_bound(request.args.get(request_params.START_DATE))
    end_date = parse_datetime_bound(
        request.args.get(request_params.END_DATE), upper=True
    )
    csv = parse_bool(request.args.get(request_params.CSV), default=False)

    formats_data = report_data.formats_count(
        storage_service_id=storage_service_id, start_date=start_date, end_date=end_date
    )
    formats = formats_data.get(fields.FIELD_FORMATS)

    headers = translate_headers(HEADERS)

    if csv:
        filename = "file_formats.csv"
        return download_csv(headers, formats, filename)

    return render_template(
        "report_formats_count.html",
        storage_service_id=storage_service_id,
        storage_service_name=formats_data.get(fields.FIELD_STORAGE_NAME),
        columns=headers,
        formats=formats,
        total_file_count=sum(format_.get(fields.FIELD_COUNT, 0) for format_ in formats),
        total_size=sum(format_.get(fields.FIELD_SIZE, 0) for format_ in formats),
        formats_count=len(formats),
        start_date=start_date,
        end_date=get_display_end_date(end_date),
    )


@reporter.route("/chart_formats_count/", methods=["GET"])
def chart_formats_count():
    """Report (pie chart) on all file formats and their counts and size
    on disk across all AIPs in the storage service."""
    start_date = request.args.get(request_params.START_DATE)
    end_date = request.args.get(request_params.END_DATE)
    # make date range inclusive
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    day_before = start - timedelta(days=1)
    day_after = end + timedelta(days=1)

    storage_service_id = request.args.get(request_params.STORAGE_SERVICE_ID)
    storage_service = StorageService.query.get(storage_service_id)
    aips = AIP.query.filter_by(storage_service_id=storage_service_id).all()

    format_labels = []
    format_counts = []
    originals_count = 0

    for aip in aips:
        original_files = File.query.filter_by(
            aip_id=aip.id, file_type=FileType.original
        )
        for original in original_files:
            if aip.create_date < day_before:
                continue
            elif aip.create_date > day_after:
                continue
            else:
                originals_count += 1
                format_labels.append(original.file_format)

    format_counts = Counter(format_labels)
    labels = list(format_counts.keys())
    values = list(format_counts.values())

    different_formats = len(format_counts.keys())

    return render_template(
        "chart_formats_count.html",
        startdate=start_date,
        enddate=end_date,
        storageService=storage_service,
        labels=labels,
        values=values,
        originalsCount=originals_count,
        differentFormats=different_formats,
    )


@reporter.route("/plot_formats_count/", methods=["GET"])
def plot_formats_count():
    """Report (scatter) on all file formats and their counts and size on
    disk across all AIPs in the storage service.
    """
    start_date = request.args.get(request_params.START_DATE)
    end_date = request.args.get(request_params.END_DATE)
    # make date range inclusive
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    day_before = start - timedelta(days=1)
    day_after = end + timedelta(days=1)

    storage_service_id = request.args.get(request_params.STORAGE_SERVICE_ID)
    storage_service = StorageService.query.get(storage_service_id)
    aips = AIP.query.filter_by(storage_service_id=storage_service_id).all()

    format_count = {}
    originals_count = 0

    for aip in aips:
        original_files = File.query.filter_by(
            aip_id=aip.id, file_type=FileType.original
        )
        for original in original_files:
            if aip.create_date < day_before:
                continue
            elif aip.create_date > day_after:
                continue
            else:
                originals_count += 1
                file_format = original.file_format
                size = original.size

                if file_format in format_count:
                    format_count[file_format]["count"] += 1
                    format_count[file_format]["size"] += size
                else:
                    format_count.update({file_format: {"count": 1, "size": size}})

    total_size = 0
    x_axis = []
    y_axis = []
    file_format = []
    human_size = []

    for _, value in format_count.items():
        y_axis.append(value["count"])
        size = value["size"]
        if size is None:
            size = 0
        x_axis.append(size)
        total_size += size
        human_size.append(filesizeformat(size))

    file_format = list(format_count.keys())
    different_formats = len(format_count.keys())
    total_human_size = filesizeformat(total_size)

    return render_template(
        "plot_formats_count.html",
        startdate=start_date,
        enddate=end_date,
        storageService=storage_service,
        originalsCount=originals_count,
        formatCount=format_count,
        differentFormats=different_formats,
        totalHumanSize=total_human_size,
        x_axis=x_axis,
        y_axis=y_axis,
        format=file_format,
        humansize=human_size,
    )
