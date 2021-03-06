# -*- coding: utf-8 -*-
import unittest

from . import horror_fobj
from nose.tools import assert_equal

from messytables import (CSVTableSet, StringType, HTMLTableSet,
                         ZIPTableSet, XLSTableSet, XLSXTableSet,
                         headers_guess, headers_processor,
                         offset_processor, DateType, FloatType,
                         IntegerType, rowset_as_jts,
                         types_processor, type_guess)


class ReadCsvTest(unittest.TestCase):
    def test_read_simple_csv(self):
        fh = horror_fobj('simple.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        assert_equal(7, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(row[0].value, 'date')
        assert_equal(row[1].value, 'temperature')

        for row in list(row_set):
            assert_equal(3, len(row))
            assert_equal(row[0].type, StringType())

    def test_read_complex_csv(self):
        fh = horror_fobj('complex.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        assert_equal(4, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(row[0].value, 'date')
        assert_equal(row[1].value, 'another date')
        assert_equal(row[2].value, 'temperature')
        assert_equal(row[3].value, 'place')

        for row in list(row_set):
            assert_equal(4, len(row))
            assert_equal(row[0].type, StringType())

    def test_overriding_sniffed(self):
        # semicolon separated values
        fh = horror_fobj('simple.csv')
        table_set = CSVTableSet(fh, delimiter=";")
        row_set = table_set.tables[0]
        assert_equal(7, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(len(row), 1)

    def test_read_head_padding_csv(self):
        fh = horror_fobj('weird_head_padding.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        offset, headers = headers_guess(row_set.sample)
        assert 11 == len(headers), headers
        assert_equal(u'1985', headers[1].strip())
        row_set.register_processor(headers_processor(headers))
        row_set.register_processor(offset_processor(offset + 1))
        data = list(row_set.sample)
        for row in row_set:
            assert_equal(11, len(row))
        value = data[1][0].value.strip()
        assert value == u'Gefäßchirurgie', value

    def test_read_head_offset_csv(self):
        fh = horror_fobj('simple.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        offset, headers = headers_guess(row_set.sample)
        assert_equal(offset, 0)
        row_set.register_processor(offset_processor(offset + 1))
        data = list(row_set.sample)
        assert_equal(int(data[0][1].value), 1)
        data = list(row_set)
        assert_equal(int(data[0][1].value), 1)

    def test_read_type_guess_simple(self):
        fh = horror_fobj('simple.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        types = type_guess(row_set.sample)
        expected_types = [DateType("%Y-%m-%d"), IntegerType(), StringType()]
        assert_equal(types, expected_types)

        row_set.register_processor(types_processor(types))
        data = list(row_set)
        header_types = map(lambda c: c.type, data[0])
        assert_equal(header_types, [StringType()] * 3)
        row_types = map(lambda c: c.type, data[2])
        assert_equal(expected_types, row_types)

    def test_apply_null_values(self):
        fh = horror_fobj('null.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        types = type_guess(row_set.sample, strict=True)
        expected_types = [IntegerType(), StringType(), IntegerType(), StringType()]
        assert_equal(types, expected_types)

        row_set.register_processor(types_processor(types))
        data = list(row_set)
        # treat null as non empty text and 0 as non empty integer
        assert [x.empty for x in data[0]] == [False, False, False, False]
        assert [x.empty for x in data[1]] == [False, False, False, False]
        assert [x.empty for x in data[2]] == [False, False, True, True]
        assert [x.empty for x in data[3]] == [False, False, False, False]
        assert [x.empty for x in data[4]] == [False, False, False, True]
        assert [x.empty for x in data[5]] == [False, False, False, True]

        # we expect None for Integers and "" for empty strings in CSV
        assert [x.value for x in data[2]] == [3, "null", None, ""], data[2]

    def test_read_encoded_csv(self):
        fh = horror_fobj('utf-16le_encoded.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        assert_equal(328, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(row[1].value, 'Organisation_name')

    def test_long_csv(self):
        fh = horror_fobj('long.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        data = list(row_set)
        assert_equal(4000, len(data))

    def test_small_csv(self):
        fh = horror_fobj('small.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        data = list(row_set)
        assert_equal(1, len(data))

    def test_skip_initials(self):
        def rows(skip_policy):
            fh = horror_fobj('skip_initials.csv')
            table_set = CSVTableSet(fh,
                                    skipinitialspace=skip_policy)
            row_set = table_set.tables[0]
            return row_set

        second = lambda r: r[1].value

        assert "goodbye" in map(second, rows(True))
        assert "    goodbye" in map(second, rows(False))

    def test_guess_headers(self):
        fh = horror_fobj('weird_head_padding.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        offset, headers = headers_guess(row_set.sample)
        row_set.register_processor(headers_processor(headers))
        row_set.register_processor(offset_processor(offset + 1))
        data = list(row_set)
        assert 'Frauenheilkunde' in data[9][0].value, data[9][0].value

        fh = horror_fobj('weird_head_padding.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        row_set.register_processor(headers_processor(['foo', 'bar']))
        data = list(row_set)
        assert 'foo' in data[12][0].column, data[12][0]
        assert 'Chirurgie' in data[12][0].value, data[12][0].value


class ReadZipTest(unittest.TestCase):
    def test_read_simple_zip(self):
        fh = horror_fobj('simple.zip')
        table_set = ZIPTableSet(fh)
        row_set = table_set.tables[0]
        assert_equal(7, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(row[0].value, 'date')
        assert_equal(row[1].value, 'temperature')

        for row in list(row_set):
            assert_equal(3, len(row))
            assert_equal(row[0].type, StringType())


class ReadTsvTest(unittest.TestCase):
    def test_read_simple_tsv(self):
        fh = horror_fobj('example.tsv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        assert_equal(141, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(row[0].value, 'hour')
        assert_equal(row[1].value, 'expr1_0_imp')
        for row in list(row_set):
            assert_equal(17, len(row))
            assert_equal(row[0].type, StringType())


class ReadSsvTest(unittest.TestCase):
    def test_read_simple_ssv(self):
        # semicolon separated values
        fh = horror_fobj('simple.ssv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        assert_equal(7, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(row[0].value, 'date')
        assert_equal(row[1].value, 'temperature')

        for row in list(row_set):
            assert_equal(3, len(row))
            assert_equal(row[0].type, StringType())


class ReadXlsTest(unittest.TestCase):
    def test_read_simple_xls(self):
        fh = horror_fobj('simple.xls')
        table_set = XLSTableSet(fh)
        assert_equal(1, len(table_set.tables))
        row_set = table_set.tables[0]
        row = list(row_set.sample)[0]
        assert_equal(row[0].value, 'date')
        assert_equal(row[1].value, 'temperature')
        assert_equal(row[2].value, 'place')

        for row in list(row_set):
            assert 3 == len(row), row

    def test_read_head_offset_excel(self):
        fh = horror_fobj('simple.xls')
        table_set = XLSTableSet(fh)
        row_set = table_set.tables[0]
        offset, headers = headers_guess(row_set.sample)
        assert_equal(offset, 0)
        row_set.register_processor(offset_processor(offset + 1))
        data = list(row_set.sample)
        assert_equal(int(data[0][1].value), 1)
        data = list(row_set)
        assert_equal(int(data[0][1].value), 1)


class ReadXlsxTest(unittest.TestCase):
    def test_read_simple_xlsx(self):
        fh = horror_fobj('simple.xlsx')
        table_set = XLSXTableSet(fh)
        assert_equal(1, len(table_set.tables))
        row_set = table_set.tables[0]
        row = list(row_set.sample)[0]
        assert_equal(row[0].value, 'date')
        assert_equal(row[1].value, 'temperature')
        assert_equal(row[2].value, 'place')

        for row in list(row_set):
            assert 3 == len(row), row

    def test_read_type_know_simple(self):
        fh = horror_fobj('simple.xls')
        table_set = XLSTableSet(fh)
        row_set = table_set.tables[0]
        row = list(row_set.sample)[1]
        types = [c.type for c in row]
        assert_equal(types, [DateType(None), FloatType(), StringType()])

    def test_bad_first_sheet(self):
        # First sheet appears to have no cells
        fh = horror_fobj('problematic_first_sheet.xls')
        table_set = XLSTableSet(fh)
        tables = table_set.tables
        assert_equal(0, len(list(tables[0].sample)))
        assert_equal(1000, len(list(tables[1].sample)))


class ReadHtmlTest(unittest.TestCase):
    def test_read_real_html(self):
        fh = horror_fobj('html.html')
        table_set = HTMLTableSet(fh)
        row_set = table_set.tables[0]
        assert_equal(200, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(row[0].value.strip(), 'HDI Rank')
        assert_equal(row[1].value.strip(), 'Country')
        assert_equal(row[4].value.strip(), '2010')

    def test_read_span_html(self):
        fh = horror_fobj('rowcolspan.html')
        table_set = HTMLTableSet(fh)
        row_set = table_set.tables[0]

        magic = {}
        for y, row in enumerate(row_set):
            for x, cell in enumerate(row):
                magic[(x, y)] = cell.value

        tests = {(0, 0): '05',
                 (0, 2): '25',
                 (0, 3): '',
                 (1, 3): '36',
                 (1, 6): '66',
                 (4, 7): '79',
                 (4, 8): '89'}

        for test in tests:
            assert_equal(magic[test], tests[test])

    def test_read_nested_html(self):
        fh = horror_fobj('complex.html')
        table_set = HTMLTableSet(fh)
        row_set = {}
        for table in table_set.tables:
            row_set[table.name] = table

        # contains_other_tables contains no meaningful data
        other = row_set['{"style": "contains_other_tables"}']
        rows = list(other)
        assert_equal(len(rows), 1)
        assert_equal(len(rows[0]), 1)
        assert_equal(rows[0][0].value.strip(), '')

    def test_read_anatomy_html(self):
        fh = horror_fobj('complex.html')
        table_set = HTMLTableSet(fh)
        row_set = {}
        for table in table_set.tables:
            row_set[table.name] = table

        # but contains_thead_tfoot_tbody has things in the right order
        anatomy = row_set['{"style": "contains_thead_tfoot_tbody"}']
        builder = []
        for row in anatomy:
            for cell in row:
                builder.append(cell.value)
        assert_equal(builder, ['head', 'body', 'foot'])

    def test_rowset_as_schema(self):
        from StringIO import StringIO as sio
        ts = CSVTableSet(sio('''name,dob\nmk,2012-01-02\n'''))
        rs = ts.tables[0]
        jts = rowset_as_jts(rs).as_dict()
        assert_equal(jts['fields'], [
            {'type': 'string', 'id': u'name', 'label': u'name'},
            {'type': 'date', 'id': u'dob', 'label': u'dob'}])
