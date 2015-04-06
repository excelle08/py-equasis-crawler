__author__ = 'Excelle'

from HTMLParser import HTMLParser
import re


class MyInfoParser(HTMLParser):
    basic_info_flag = False
    basic_info_flag_2 = False
    ext_info_title_begin = False
    ext_info_title_end = False
    ext_info_start = False
    current_ext_tag = ''
    _list_basic_info = []
    _list_overview = []
    _list_manage_detail = []
    _list_class_stat = []
    _list_class_survey = []
    _list_pi = []
    _list_geo = []
    _list_smc = []
    _list_imo_convention = []
    _list_psc_list = []
    _list_psc_info = []
    _list_deficiencies = []
    _list_history_name = []
    _list_history_flag = []
    _list_history_class = []
    _list_history_company = []
    _list_company_overview = []
    _list_doc_compliance = []
    _list_synthesis_insp = []
    _list_fleet = []
    _list_class_key = []
    company_ids = []
    insp_ids = []

    def __init__(self):
        self._list_basic_info = []
        self._lit_overview = []
        self._lit_manage_detail = []
        self._lit_class_stat = []
        self._lit_class_survey = []
        self._lit_pi = []
        self._list_geo = []
        self._list_smc = []
        self._list_imo_convention = []
        self._list_psc_list = []
        self._list_psc_info = []
        self._list_deficiencies = []
        self._list_history_name = []
        self._list_history_flag = []
        self._list_history_class = []
        self._list_history_company = []
        self._list_company_overview = []
        self._list_doc_compliance = []
        self._list_synthesis_insp = []
        self._list_fleet = []
        self._list_class_key = []
        self.reset()

    def handle_starttag(self, tag, attrs):
        attr = dict()
        attr['class'] = ''
        attr['src'] = ''
        attr['onclick'] = ''
        for key, value in attrs:
            attr[key] = value
        if tag == 'td' and attr['class'] == 'bleugras':
            self.basic_info_flag = True
            self.basic_info_flag_2 = False
            return
        if tag == 'td' and self.basic_info_flag:
            self.basic_info_flag = False
            self.basic_info_flag_2 = True
        if tag == 'img' and attr['src'] == '../Static/img/puce_triangle_tit.gif':
            self.ext_info_title_begin = True
            self.ext_info_title_end = False
            return
        if tag == 'a' and re.search('document.formShip.P_COMP.value', attr['onclick']):
            r = re.search(r'P_COMP.value=\'(\d+)\'', attr['onclick'])
            self.company_ids.append(r.group(1))
        if tag == 'a' and re.search('document.formShip.P_INSP.value', attr['onclick']):
            r = re.search(r'P_INSP.value=\'(\d+)\'', attr['onclick'])
            self.insp_ids.append(r.group(1))
        if tag == 'tr' and (attr['class'] == 'lignej' or attr['class'] == 'ligneb'):
            self.ext_info_start = True
            return

    def handle_endtag(self, tag):
        if self.ext_info_start and tag == 'tr':
            self.ext_info_start = False
        pass

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_data(self, data):
        if self.basic_info_flag and not self.basic_info_flag_2:
            self._list_basic_info.append(data)
        if self.basic_info_flag_2 and not self.basic_info_flag:
            self._list_basic_info.append(data)
            self.basic_info_flag_2 = False
        if self.ext_info_title_begin and not self.ext_info_title_end:
            self.current_ext_tag = data
            self.ext_info_title_end = True
            self.ext_info_title_begin = False
        if self.ext_info_start:
            if re.search('OVERVIEW', self.current_ext_tag):
                self._list_overview.append(data)
            elif re.search('Management', self.current_ext_tag):
                self._list_manage_detail.append(data)
            elif re.search('Classification status', self.current_ext_tag):
                self._list_class_stat.append(data)
            elif re.search('Classification survey', self.current_ext_tag):
                self._list_class_survey.append(data)
            elif re.search('P/I', self.current_ext_tag):
                self._list_pi.append(data)
            elif re.search('Geographical', self.current_ext_tag):
                self._list_geo.append(data)
            elif re.search('Safety management certificate', self.current_ext_tag):
                self._list_smc.append(data)
            elif re.search('Show IMO conventions signed by the state', self.current_ext_tag):
                self._list_imo_convention.append(data)
            elif re.search('List of port state controls', self.current_ext_tag):
                self._list_psc_list.append(data)
            elif re.search('Current and former name\(s\)', self.current_ext_tag):
                self._list_history_name.append(data)
            elif re.search('Current and former flag\(s\)', self.current_ext_tag):
                self._list_history_flag.append(data)
            elif re.search('List of class renewal surveys', self.current_ext_tag):
                self._list_history_class.append(data)
            elif re.search('Company', self.current_ext_tag):
                self._list_history_company.append(data)
            elif re.search('Number of deficiencies', self.current_ext_tag):
                self._list_deficiencies.append(data)
            elif re.search('Documents of compliance', self.current_ext_tag):
                self._list_doc_compliance.append(data)
            elif re.search('Overview', self.current_ext_tag):
                self._list_company_overview.append(data)
            elif re.search('Synthesis of inspections', self.current_ext_tag):
                self._list_synthesis_insp.append(data)
            elif re.search('Fleet', self.current_ext_tag):
                self._list_fleet.append(data)
            elif re.search('Class key', self.current_ext_tag):
                self._list_class_key.append(data)

    def handle_entityref(self, name):
        if self.ext_info_start:
            print('%s : <&%s>' % (self.current_ext_tag, name))

    def get_basic_info(self):
        res = []
        for i in range(0, self._list_basic_info.__len__()):
            res.append(self._list_basic_info.pop(0))
        return res

    def get_company_ids(self):
        res = []
        for i in range(0, self.company_ids.__len__()):
            res.append(self.company_ids.pop())
        return res

    def get_manage_detail(self):
        res = []
        for i in range(0, self._list_manage_detail.__len__()):
            res.append(self._list_manage_detail.pop(0))
        return res

    def get_class_status(self):
        res = []
        for i in range(0, self._list_class_stat.__len__()):
            res.append(self._list_class_stat.pop(0))
        return res

    def get_class_survey(self):
        res = []
        for i in range(0, self._list_class_survey.__len__()):
            res.append(self._list_class_survey.pop(0))
        return res

    def get_pi_info(self):
        res = []
        for i in range(0, self._list_pi.__len__()):
            res.append(self._list_pi.pop(0))
        return res

    def get_geographical_info(self):
        res = []
        for i in range(0, self._list_geo.__len__()):
            res.append(self._list_geo.pop(0))
        return res

    def get_overview(self):
        res = []
        for i in range(0, self._list_overview.__len__()):
            res.append(self._list_overview.pop(0))
        return res

    def get_smc(self):
        res = []
        for i in range(0, self._list_smc.__len__()):
            res.append(self._list_smc.pop(0))
        return res

    def get_imo_convention(self):
        res = []
        for i in range(0, self._list_imo_convention.__len__()):
            res.append(self._list_imo_convention.pop(0))
        return res

    def get_psc_list(self):
        res = []
        for i in range(0, self._list_psc_list.__len__()):
            res.append(self._list_psc_list.pop(0))
        return res

    def get_psc_info(self):
        res = []
        for i in range(0, self._list_psc_info.__len__()):
            res.append(self._list_psc_info.pop(0))
        return res

    def get_deficiencies(self):
        res = []
        for i in range(0, self._list_deficiencies.__len__()):
            res.append(self._list_deficiencies.pop(0))
        return res

    def get_history_name(self):
        res = []
        for i in range(0, self._list_history_name.__len__()):
            res.append(self._list_history_name.pop(0))
        return res

    def get_history_flag(self):
        res = []
        for i in range(0, self._list_history_flag.__len__()):
            res.append(self._list_history_flag.pop(0))
        return res

    def get_history_class(self):
        res = []
        for i in range(0, self._list_history_class.__len__()):
            res.append(self._list_history_class.pop(0))
        return res

    def get_history_company(self):
        res = []
        for i in range(0, self._list_history_company.__len__()):
            res.append(self._list_history_company.pop(0))
        return res

    def get_company_overview(self):
        res = []
        for i in range(0, self._list_company_overview.__len__()):
            res.append(self._list_company_overview.pop(0))
        return res

    def get_doc_compliance(self):
        res = []
        for i in range(0, self._list_doc_compliance.__len__()):
            res.append(self._list_doc_compliance.pop(0))
        return res

    def get_synthesis_insp(self):
        res = []
        for i in range(0, self._list_synthesis_insp.__len__()):
            res.append(self._list_synthesis_insp.pop(0))
        return res

    def get_fleet(self):
        res = []
        for i in range(0, self._list_fleet.__len__()):
            res.append(self._list_fleet.pop(0))
        return res

    def get_class_key(self):
        res = []
        for i in range(0, self._list_class_key.__len__()):
            res.append(self._list_class_key.pop(0))
        return res

    def get_insp_id(self):
        res = []
        for i in range(0, self.insp_ids.__len__()):
            res.append(self.insp_ids.pop())
        return res

    def dispose(self):
        self._list_basic_info = None
        self._list_manage_detail = None
        self._list_class_stat = None
        self._list_class_survey = None
        self._list_overview = None
        self._list_pi = None
        self._list_geo = None
        self._list_smc = None
        self._list_imo_convention = None
        self._list_psc_list = None
        self._list_psc_info = None
        self._list_deficiencies = None
        self._list_history_name = None
        self._list_history_flag = None
        self._list_history_class = None
        self._list_history_company = None
        self._list_company_overview = None
        self._list_doc_compliance = None
        self._list_synthesis_insp = None
        self._list_fleet = None
        self._list_class_key = None