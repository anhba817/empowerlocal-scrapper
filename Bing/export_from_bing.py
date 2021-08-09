from auth_helper import *
from bingads.v13.reporting import *

import argparse
import sys, calendar, csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# import logging
# logging.basicConfig(level=logging.INFO)
# logging.getLogger('suds.client').setLevel(logging.DEBUG)
# logging.getLogger('suds.transport.http').setLevel(logging.DEBUG)

# You must provide credentials in auth_helper.py.

# The report file extension type.
REPORT_FILE_FORMAT='Csv'

# The directory for the report files.
FILE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

# The name of the report download file.
RESULT_FILE_NAME='result.' + REPORT_FILE_FORMAT.lower()

# The maximum amount of time (in milliseconds) that you want to wait for the report download.
TIMEOUT_IN_MILLISECONDS=3600000


scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name(FILE_DIRECTORY + '/../google_sheet_secret.json', scope)
gsclient = gspread.authorize(credentials)

def parse_args(args):
    parser = argparse.ArgumentParser(description='Scrap data from mailchimp.')
    parser.add_argument("-m", "--month", type=int, help="Month")
    parser.add_argument("-y", "--year", type=int, help="Year")
    return parser.parse_args(args)

def main(authorization_data):
    try:
        # You can submit one of the example reports, or build your own.

        report_request=get_report_request(authorization_data.account_id)

        reporting_download_parameters = ReportingDownloadParameters(
            report_request=report_request,
            result_file_directory = FILE_DIRECTORY,
            result_file_name = RESULT_FILE_NAME,
            overwrite_result_file = True, # Set this value true if you want to overwrite the same file.
            timeout_in_milliseconds=TIMEOUT_IN_MILLISECONDS # You may optionally cancel the download after a specified time interval.
        )

        #Option A - Background Completion with ReportingServiceManager
        #You can submit a download request and the ReportingServiceManager will automatically
        #return results. The ReportingServiceManager abstracts the details of checking for result file
        #completion, and you don't have to write any code for results polling.

        #output_status_message("-----\nAwaiting Background Completion...")
        #background_completion(reporting_download_parameters)

        #Option B - Submit and Download with ReportingServiceManager
        #Submit the download request and then use the ReportingDownloadOperation result to
        #track status yourself using ReportingServiceManager.get_status().

        #output_status_message("-----\nAwaiting Submit and Download...")
        #submit_and_download(report_request)

        #Option C - Download Results with ReportingServiceManager
        #If for any reason you have to resume from a previous application state,
        #you can use an existing download request identifier and use it
        #to download the result file.

        #For example you might have previously retrieved a request ID using submit_download.
        #reporting_operation=reporting_service_manager.submit_download(report_request)
        #request_id=reporting_operation.request_id

        #Given the request ID above, you can resume the workflow and download the report.
        #The report request identifier is valid for two days.
        #If you do not download the report within two days, you must request the report again.
        #output_status_message("-----\nAwaiting Download Results...")
        #download_results(request_id, authorization_data)

        #Option D - Download the report in memory with ReportingServiceManager.download_report
        #The download_report helper function downloads the report and summarizes results.
        output_status_message("-----\nAwaiting download_report...")
        download_report(reporting_download_parameters)

        # UPLOAD TO GOOGLE SHEET
        spreadsheet = gsclient.open_by_key('1ZFFq-t267vXIxivxK0KTTlOj9p_-ynS6W4zaOidg9U8')
        with open('result.csv', 'r') as file_obj:
            content = file_obj.read()
            gsclient.import_csv(spreadsheet.id, data=content.encode(encoding='utf-8'))

    except WebFault as ex:
        output_webfault_errors(ex)
    except Exception as ex:
        output_status_message(ex)


def background_completion(reporting_download_parameters):
    """ You can submit a download request and the ReportingServiceManager will automatically
    return results. The ReportingServiceManager abstracts the details of checking for result file
    completion, and you don't have to write any code for results polling. """

    global reporting_service_manager
    result_file_path = reporting_service_manager.download_file(reporting_download_parameters)
    output_status_message("Download result file: {0}".format(result_file_path))

def submit_and_download(report_request):
    """ Submit the download request and then use the ReportingDownloadOperation result to
    track status until the report is complete e.g. either using
    ReportingDownloadOperation.track() or ReportingDownloadOperation.get_status(). """

    global reporting_service_manager
    reporting_download_operation = reporting_service_manager.submit_download(report_request)

    # You may optionally cancel the track() operation after a specified time interval.
    reporting_operation_status = reporting_download_operation.track(timeout_in_milliseconds=TIMEOUT_IN_MILLISECONDS)

    # You can use ReportingDownloadOperation.track() to poll until complete as shown above,
    # or use custom polling logic with get_status() as shown below.
    #for i in range(10):
    #    time.sleep(reporting_service_manager.poll_interval_in_milliseconds / 1000.0)

    #    download_status = reporting_download_operation.get_status()

    #    if download_status.status == 'Success':
    #        break

    result_file_path = reporting_download_operation.download_result_file(
        result_file_directory = FILE_DIRECTORY,
        result_file_name = RESULT_FILE_NAME,
        decompress = True,
        overwrite = True,  # Set this value true if you want to overwrite the same file.
        timeout_in_milliseconds=TIMEOUT_IN_MILLISECONDS # You may optionally cancel the download after a specified time interval.
    )

    output_status_message("Download result file: {0}".format(result_file_path))

def download_results(request_id, authorization_data):
    """ If for any reason you have to resume from a previous application state,
    you can use an existing download request identifier and use it
    to download the result file. Use ReportingDownloadOperation.track() to indicate that the application
    should wait to ensure that the download status is completed. """

    reporting_download_operation = ReportingDownloadOperation(
        request_id = request_id,
        authorization_data=authorization_data,
        poll_interval_in_milliseconds=1000,
        environment=ENVIRONMENT,
    )

    # Use track() to indicate that the application should wait to ensure that
    # the download status is completed.
    # You may optionally cancel the track() operation after a specified time interval.
    reporting_operation_status = reporting_download_operation.track(timeout_in_milliseconds=TIMEOUT_IN_MILLISECONDS)

    result_file_path = reporting_download_operation.download_result_file(
        result_file_directory = FILE_DIRECTORY,
        result_file_name = RESULT_FILE_NAME,
        decompress = True,
        overwrite = True,  # Set this value true if you want to overwrite the same file.
        timeout_in_milliseconds=TIMEOUT_IN_MILLISECONDS # You may optionally cancel the download after a specified time interval.
    )

    output_status_message("Download result file: {0}".format(result_file_path))
    output_status_message("Status: {0}".format(reporting_operation_status.status))

def download_report(reporting_download_parameters):
    """ You can get a Report object by submitting a new download request via ReportingServiceManager.
    Although in this case you will not work directly with the file, under the covers a request is
    submitted to the Reporting service and the report file is downloaded to a local directory.  """

    global reporting_service_manager

    report_container = reporting_service_manager.download_report(reporting_download_parameters)

    #Otherwise if you already have a report file that was downloaded via the API,
    #you can get a Report object via the ReportFileReader.

    # report_file_reader = ReportFileReader(
    #     file_path = reporting_download_parameters.result_file_directory + reporting_download_parameters.result_file_name,
    #     format = reporting_download_parameters.report_request.Format)
    # report_container = report_file_reader.get_report()

    if(report_container == None):
        output_status_message("There is no report data for the submitted report request parameters.")
        sys.exit(0)

    #Once you have a Report object via either workflow above, you can access the metadata and report records.

    output_status_message("Successfully download report from Bing")
    report_container.close()

def get_report_request(account_id):
    """
    Use a sample report request or build your own.
    """

    aggregation = 'Daily'
    exclude_column_headers=False
    exclude_report_footer=True
    exclude_report_header=True
    time=reporting_service.factory.create('ReportTime')
    # You can either use a custom date range or predefined time.
    custom_date_range_start=reporting_service.factory.create('Date')
    custom_date_range_start.Day=1
    custom_date_range_start.Month=7
    custom_date_range_start.Year=2021
    time.CustomDateRangeStart=custom_date_range_start
    custom_date_range_end=reporting_service.factory.create('Date')
    custom_date_range_end.Day=31
    custom_date_range_end.Month=7
    custom_date_range_end.Year=2021
    time.CustomDateRangeEnd=custom_date_range_end
    time.PredefinedTime=None
    return_only_complete_data=False

    keyword_performance_report_request=get_keyword_performance_report_request(
        account_id=account_id,
        aggregation=aggregation,
        exclude_column_headers=exclude_column_headers,
        exclude_report_footer=exclude_report_footer,
        exclude_report_header=exclude_report_header,
        report_file_format=REPORT_FILE_FORMAT,
        return_only_complete_data=return_only_complete_data,
        time=time)

    return keyword_performance_report_request

def get_keyword_performance_report_request(
        account_id,
        aggregation,
        exclude_column_headers,
        exclude_report_footer,
        exclude_report_header,
        report_file_format,
        return_only_complete_data,
        time):

    report_request=reporting_service.factory.create('KeywordPerformanceReportRequest')
    report_request.Aggregation=aggregation
    report_request.ExcludeColumnHeaders=exclude_column_headers
    report_request.ExcludeReportFooter=exclude_report_footer
    report_request.ExcludeReportHeader=exclude_report_header
    report_request.Format=report_file_format
    report_request.ReturnOnlyCompleteData=return_only_complete_data

    report_request.Time=time

    report_request.ReportName="EL Accounts by Day"
    scope=reporting_service.factory.create('AccountReportScope')
    scope.AccountIds={'long': account_id }
    # scope.Campaigns=None
    # scope.AdGroups=None
    report_request.Scope=scope

    report_filter = reporting_service.factory.create('KeywordPerformanceReportFilter')
    report_filter.AccountStatus = "Active"
    report_request.Filter = report_filter

    report_columns=reporting_service.factory.create('ArrayOfKeywordPerformanceReportColumn')
    report_columns.KeywordPerformanceReportColumn.append([
        'TimePeriod',
        # 'AccountNumber',
        'AccountName',
        'Impressions',
        'Clicks',
        'Ctr',
        'AverageCpc',
        'Spend',
        'TopImpressionRatePercent',
        'AbsoluteTopImpressionRatePercent',
        'Conversions',
        'ConversionRate',
        'CostPerConversion'
    ])
    report_request.Columns=report_columns

    return report_request

# Main execution
if __name__ == '__main__':
    arguments = parse_args(sys.argv[1:])

    month = arguments.month
    year = arguments.year
    today = datetime.today()
    if not month:
        month = today.month - 1 if today.month != 1 else 12
    if not year:
        year = today.year if today.month != 1 else today.year - 1

    last_day_in_month = calendar.monthrange(year, month)[1]

    print("Loading the web service client proxies...")

    authorization_data=AuthorizationData(
        account_id=bing_auth["account_id"],
        customer_id=bing_auth["customer_id"],
        developer_token=bing_auth["developer_token"],
        authentication=None,
    )

    reporting_service_manager=ReportingServiceManager(
        authorization_data=authorization_data,
        poll_interval_in_milliseconds=5000,
        environment=ENVIRONMENT,
    )

    # In addition to ReportingServiceManager, you will need a reporting ServiceClient
    # to build the ReportRequest.

    reporting_service=ServiceClient(
        service='ReportingService',
        version=13,
        authorization_data=authorization_data,
        environment=ENVIRONMENT,
    )

    authenticate(authorization_data)

    main(authorization_data)