$(document).ready(function() {
  
  // Download CSV of current report
  $('#downloadCSV').on('click', function() {
    window.location.href = window.location.href + '&csv=True';
  });

  // Reload largest files report on change to file type dropdown
  $("#fileTypeSelector").on("change", function() {
    var fileType = $('#fileTypeSelector').val();
    var storageServiceId = $('#storageServiceID').text();
    var storageLocationId = $('#storageLocationID').text();
    var startDate = $('#startDate').text();
    var endDate = $('#endDate').text();
    var limit = $('#limit').text();
    var url = (
      window.location.origin +
      '/reporter/largest_files?' +
      'amss_id=' +
      storageServiceId +
      '&start_date=' +
      startDate +
      '&end_date=' +
      endDate +
      '&storage_location=' +
      storageLocationId +
      '&file_type=' +
      fileType +
      '&limit=' +
      limit
    );
    window.location.href = url;
  });

  // Reload preservation derivatives report on change to AIP dropdown
  $("#aipSelector").on("change", function() {
    var aipUUID = $('#aipSelector').val();
    var storageServiceId = $('#storageServiceID').text();
    var storageLocationId = $('#storageLocationID').text();
    var url = (
      window.location.origin +
      '/reporter/preservation_derivatives?' +
      'amss_id=' +
      storageServiceId +
      '&storage_location=' +
      storageLocationId +
      '&aip_uuid=' +
      aipUUID
    );
    window.location.href = url;
  });

  // Reload storage locations timeseries report on change to metrics or
  // cumulative selectors
  $("#metricSelector").on("change", function() {
    var metric = $('#metricSelector').val();
    var cumulative = $('#cumulativeSelector').val();
    var storageServiceId = $('#storageServiceID').text();
    var startDate = $('#startDate').text();
    var endDate = $('#endDate').text();
    var url = (
      window.location.origin +
      '/reporter/storage_locations_usage_over_time?' +
      'amss_id=' +
      storageServiceId +
      '&start_date=' +
      startDate +
      '&end_date=' +
      endDate +
      '&metric=' +
      metric +
      '&cumulative=' +
      cumulative
    );
    window.location.href = url;
  });

  $("#cumulativeSelector").on("change", function() {
    var metric = $('#metricSelector').val();
    var cumulative = $('#cumulativeSelector').val();
    var storageServiceId = $('#storageServiceID').text();
    var startDate = $('#startDate').text();
    var endDate = $('#endDate').text();
    var url = (
      window.location.origin +
      '/reporter/storage_locations_usage_over_time?' +
      'amss_id=' +
      storageServiceId +
      '&start_date=' +
      startDate +
      '&end_date=' +
      endDate +
      '&metric=' +
      metric +
      '&cumulative=' +
      cumulative
    );
    window.location.href = url;
  });

});
