# -*- coding: utf-8 -*-

"""Report on original copies that have a preservation derivative and
the different file formats associated with both.
"""

from flask import render_template, request

from AIPscan.Data import data
from AIPscan.Reporter import reporter, translate_headers, request_params


@reporter.route("/original_derivatives/", methods=["GET"])
def original_derivatives():
    """Return a mapping between original files and derivatives if they
    exist.
    """
    aips_with_preservation_files = []
    storage_service_id = request.args.get(request_params["storage_service_id"])
    derivative_data = data.derivative_overview(storage_service_id=storage_service_id)
    storage_service_name = derivative_data[data.FIELD_STORAGE_NAME]

    for aip in derivative_data[data.FIELD_ALL_AIPS]:
        aip_info = {}
        aip_info[data.FIELD_TRANSFER_NAME] = aip[data.FIELD_TRANSFER_NAME]
        aip_info[data.FIELD_UUID] = aip[data.FIELD_UUID]
        aip_info[data.FIELD_DERIVATIVE_COUNT] = aip[data.FIELD_DERIVATIVE_COUNT]
        aip_info["table_data"] = []
        for pairing in aip[data.FIELD_RELATED_PAIRING]:
            row = []
            row.append(pairing[data.FIELD_ORIGINAL_UUID])
            row.append(pairing[data.FIELD_ORIGINAL_FORMAT])
            row.append(pairing[data.FIELD_DERIVATIVE_UUID])
            row.append(pairing[data.FIELD_DERIVATIVE_FORMAT])
            aip_info["table_data"].append(row)
        aips_with_preservation_files.append(aip_info)
    headers = [
        data.FIELD_ORIGINAL_UUID,
        data.FIELD_ORIGINAL_FORMAT,
        data.FIELD_DERIVATIVE_UUID,
        data.FIELD_DERIVATIVE_FORMAT,
    ]
    return render_template(
        "report_originals_derivatives.html",
        storage_service=storage_service_id,
        storage_service_name=storage_service_name,
        aip_count=len(aips_with_preservation_files),
        headers=translate_headers(headers),
        aips=aips_with_preservation_files,
    )
