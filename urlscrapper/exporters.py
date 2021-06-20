from scrapy.exporters import CsvItemExporter

class MyCsvItemExporter(CsvItemExporter):
    header_map = {
        'client': 'Client',
        'article': 'Page',
        'date': 'Date of Publish',
        'title': 'Page Title'
    }

    def _write_headers_and_set_fields_to_export(self, item):
        if not self.include_headers_line:
            return
        # this is the parent logic taken from parent class
        if not self.fields_to_export:
            if isinstance(item, dict):
                # for dicts try using fields of the first item
                self.fields_to_export = list(item.keys())
            else:
                # use fields declared in Item
                self.fields_to_export = list(item.fields.keys())
        headers = list(self._build_row(self.fields_to_export))

        # here we add our own extra mapping
        # map headers to our value
        headers = [self.header_map.get(header, header) for header in headers]
        self.csv_writer.writerow(headers)