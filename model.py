__author__ = 'Excelle'

from logger import log
import time
import sqlite3
import re
import random

cursor = None
conn = None


def initSQLDb():
    global cursor, conn
    conn = sqlite3.connect('equasis.db', timeout=30.0)
    cursor = conn.cursor()
    try:
        with open('db.sql', 'r') as f:
            init_table_sql = f.read()
        init_table_sql = init_table_sql.replace('\n', '')
        sql_cmd = init_table_sql.split(';')
        for i in sql_cmd:
            cursor.execute(i)
    except sqlite3.OperationalError, e:
        pass
    conn.commit()


def close_db():
    global cursor, conn
    cursor.close()
    conn.close()


def clear_list(lst):
    while lst.__len__():
        lst.pop(0)


def addslashes(str):
    return str.replace('\'', '\\\'').replace('"', '\\"').replace('\\', '\\\\')


class Ship():
    imo_number = 0
    name = ''
    mmsi = 0
    dwt = ''
    call_sign = ''
    tonnage = 0
    type = ''
    build_year = 0
    flag = ''
    status = ''
    last_update = ''
    overview_list = []
    management_detail_list = []
    classification_status = []
    classification_survey = []
    smc_info = []
    pi_info = []
    geo_info = []
    imo_convention = list()
    psc_info = list()
    list_psc = list()
    list_deficiencies = list()
    history_name = list()
    history_flag = list()
    history_class = list()
    history_company = list()
    company_overview = list()
    company_info = list()
    doc_compliance = list()
    synthesis_inspection = list()
    fleet = list()
    class_key = list()

    def add_overview(self, content, value):
        content = addslashes(content)
        value = addslashes(value)
        self.overview_list.append(dict(overview=content, value=value))

    def add_management(self, imo, role, company, address, date):
        imo = addslashes(imo)
        role = addslashes(role)
        company= addslashes(company)
        address = addslashes(address)
        date = addslashes(date)
        self.management_detail_list.append(dict(imo_num=imo, role=role, company=company,
                                                address=address, date_of_effect=date))

    def add_class_stat(self, society, date, status, reason):
        society = addslashes(society)
        date = addslashes(date)
        status = addslashes(status)
        reason = addslashes(reason)
        self.classification_status.append(dict(class_society=society, date_change_stat=date,
                                               status=status, reason=reason))

    def add_class_survey(self, society, date, date_next, detail):
        society = addslashes(society)
        date = addslashes(date)
        date_next = addslashes(date_next)
        self.classification_survey.append(dict(class_society=society, date_last=date,
                                               date_next=date_next, detail=detail))

    def add_smc(self, society, date_survey, date_expiry, date_change, status, reason, cv):
        self.smc_info.append(dict(class_society=addslashes(society), date_survey=addslashes(date_survey),
                                  date_expiry=addslashes(date_expiry), date_change=addslashes(date_change),
                                  status=addslashes(status), reason=addslashes(reason), cv=addslashes(cv)))

    def add_pi(self, insurer, date):
        self.pi_info.append(dict(insurer=addslashes(insurer), date_inception=addslashes(date)))

    def add_geo(self, date, area, source):
        self.geo_info.append(dict(date_record=addslashes(date), seen_area=addslashes(area),
                                  source=addslashes(source)))

    def add_imo_convention(self, convention, status):
        self.imo_convention.append(dict(convention=addslashes(convention), status=addslashes(status)))

    def add_psc_info(self, build_year, tonnage, deadweight, type_ship, flag_ship, class_society,
                     particular_company, name_authority, place_insp, date_insp, ship_detained, num_deficiencies):

        self.psc_info.append(dict(year_of_build=build_year, tonnage=tonnage, deadweight=deadweight,
                                  type_ship=type_ship,flag_ship=flag_ship, particular_of_company=particular_company,
                                  name_authority=name_authority, place_insp=place_insp, date_insp=date_insp,
                                  ship_detained=ship_detained, num_deficiencies=num_deficiencies,
                                  class_society=class_society))

    def add_psc_list(self, psc_org, authority, port, insp_type, date_report, detention, duration, num_deficiencies):
        psc_org = addslashes(psc_org)
        authority = addslashes(authority)
        port = addslashes(port)
        insp_type = addslashes(insp_type)
        date_report = addslashes(date_report)
        detention = addslashes(detention)
        duration = addslashes(duration)
        num_deficiencies = addslashes(num_deficiencies)
        self.list_psc.append(dict(psc_org=psc_org, authority=authority, port_of_insp=port, type_of_insp=insp_type,
                                  date_report=date_report, detention=detention, duration=duration,
                                  num_deficiencies=num_deficiencies))

    def add_deficiency(self, category, deficiency, number):
        category = addslashes(category)
        deficiency = addslashes(deficiency)
        number = addslashes(number)
        self.list_deficiencies.append(dict(category=category, deficiency=deficiency, number=number))

    def add_history_name(self, former_name, date_effect, source):
        former_name = addslashes(former_name)
        date_effect = addslashes(date_effect)
        self.history_name.append(dict(former_name=former_name, date_effect=date_effect, source=source))

    def add_history_flag(self, flag, date_effect, source):
        flag = addslashes(flag)
        date_effect = addslashes(date_effect)
        source = addslashes(source)
        self.history_flag.append(dict(flag=flag, date_effect=date_effect, source=source))

    def add_history_class(self, society, date_survey, source):
        society = addslashes(society)
        date_survey = addslashes(date_survey)
        source = addslashes(source)
        self.history_class.append(dict(class_society=society, date_survey=date_survey, source=source))

    def add_history_company(self, company, role, date_effect, source):
        company = addslashes(company)
        role = addslashes(role)
        date_effect = addslashes(date_effect)
        source = addslashes(source)
        self.history_company.append(dict(company=company, role=role, date_effect=date_effect, source=source))

    def add_company_overview(self, imo, overview, value):
        overview = addslashes(overview)
        value = addslashes(value)
        self.company_overview.append(dict(imo_company=imo, overview=overview, value=value))

    def add_doc_compliance(self, imo, flag, ship_type, society, status, date_of_status, reason):
        flag = addslashes(flag)
        ship_type = addslashes(ship_type)
        society = addslashes(society)
        status = addslashes(status)
        date_of_status = addslashes(date_of_status)
        reason = addslashes(reason)
        self.doc_compliance.append(dict(imo_company=imo, flag=flag, ship_type=ship_type,
                                        class_society=society, status=status, date_of_status=date_of_status,
                                        reason=reason))

    def add_fleet(self, imo_company, imo_ship_name, tonnage, ship_type, year_build, current_flag,
                  current_class, detentions_3yr_this_comp, detentions_3yr_all_comp, acting_as):
        imo_company = addslashes(imo_company)
        tonnage = addslashes(tonnage)
        ship_type = addslashes(ship_type)
        year_build = addslashes(year_build)
        current_class = addslashes(current_class)
        acting_as = addslashes(acting_as)
        self.fleet.append(dict(imo_company=imo_company, imo_ship_name=imo_ship_name, tonnage=tonnage,
                               ship_type=ship_type, year_build=year_build, current_flag=current_flag,
                               current_class=current_class, detentions_3yr_all_comp=detentions_3yr_all_comp,
                               detentions_3yr_this_comp=detentions_3yr_this_comp, acting_as=acting_as))

    def add_class_key(self, imo_company, abbr, name_of_society):
        self.class_key.append(dict(imo_company=imo_company, abbr=abbr, name_of_society=name_of_society))

    def add_synthesis_inspection(self, imo_company, role, nb_ships, last_3y_this_company_insp,
                                 last_3y_this_company_dete, last_3y_all_company_insp, last_3y_all_company_dete):
        role = addslashes(role)
        self.synthesis_inspection.append(dict(imo_company=imo_company, role=role, nb_ships=nb_ships,
                                              last_3y_all_company_dete=last_3y_all_company_dete,
                                              last_3y_all_company_insp=last_3y_all_company_insp,
                                              last_3y_this_company_dete=last_3y_this_company_dete,
                                              last_3y_this_company_insp=last_3y_this_company_insp))

    def add_company_info(self, imo, name, address, last_update):
        self.company_info.append(dict(imo_company=imo, name=addslashes(name),
                                      address=addslashes(address), last_update=last_update))

    def Commit(self):
        global cursor, conn
        sql = ''
        try:
            # Insert basic info table
            sql = 'insert into ships (`imo_number`, `name`, `mmsi`, `call_sign`, `tonnage`, `DWT`, `type`,' \
                  '`build_year`, `flag`, `status`, `last_update_time`) VALUES' \
                  '(%s, "%s", %s, "%s", %s, "%s", "%s",' \
                  ' %s, "%s", "%s", "%s");' % \
                  (self.imo_number, self.name, self.mmsi, self.call_sign,
                   self.tonnage, self.dwt, self.type, self.build_year, self.flag, self.status, self.last_update, )
            cursor.execute(sql)
            # Insert overview table
            for i in self.overview_list:
                sql = 'insert into overview (`imo_number`, `name`, `mmsi`, `call_sign`, `overview`, `value`) VALUES' \
                      '(%s, "%s", %s, "%s", "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['overview'], i['value'])
                cursor.execute(sql)
            # Insert Management detail table
            for i in self.management_detail_list:
                sql = 'insert into management_detail (`imo_number_ship`, `name_ship`, `mmsi`, `call_sign`, `imo_company`,' \
                      '`role`, `name_company`, `address`, `date_effect`) values' \
                      '(%s, "%s", %s, "%s", "%s", "%s", "%s", "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['imo_num'], i['role'], i['company'],
                       i['address'], i['date_of_effect'])
                cursor.execute(sql)
            # Insert class status table
            for i in self.classification_status:
                sql = 'insert into classification_status (`imo_number`, `name`, `mmsi`, `call_sign`,' \
                      '`class_society`, `date_change_status`, `status`, `reason`) values' \
                      '(%s, "%s", %s, "%s", "%s", "%s", "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['class_society'], i['date_change_stat'],
                       i['status'], i['reason'])
                cursor.execute(sql)
            # Insert classification survey table
            for i in self.classification_survey:
                sql = 'insert into classification_survey (`imo_number`, `name`, `mmsi`, `call_sign`,' \
                      '`class_society`, `last_renew_date`, `next_renew_date`) VALUES' \
                      '(%s, "%s", %s, "%s", "%s", "%s", "%s")' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['class_society'], i['date_last'],
                       i['date_next'])
                cursor.execute(sql)
            # Insert PI table
            for i in self.pi_info:
                sql = 'insert into pi_info (`imo_number`, `name`, `mmsi`, `call_sign`, `name_insurer`, `date_inception`)' \
                      'values (%s, "%s", %s, "%s", "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['insurer'], i['date_inception'])
                cursor.execute(sql)
            # Insert Geographical info table
            for i in self.geo_info:
                sql = 'insert into geo_info (`imo_number`, `name`, `mmsi`, `call_sign`,' \
                      '`date_record`, `area`, `source`) values' \
                      '(%s, "%s", %s, "%s", "%s", "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['date_record'],
                       i['seen_area'], i['source'])
                cursor.execute(sql)
            # Insert SMC info table
            for i in self.smc_info:
                sql = 'insert into smc (`imo_number`, `name`, `mmsi`, `call_sign`, `class_society`,' \
                      '`date_survey`, `date_expiry`, `date_change_status`,' \
                      '`status`, `reason`, `cv`) values' \
                      '(%s, "%s", %s, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s");' % \
                       (self.imo_number, self.name, self.mmsi, self.call_sign, i['class_society'],
                        i['date_survey'], i['date_expiry'], i['date_change'], i['status'],
                        i['reason'], i['cv'])
                cursor.execute(sql)
            # Insert IMO Conventions table
            for i in self.imo_convention:
                sql = 'insert into imo_conventions (`imo_number`, `name`, `mmsi`, `call_sign`,' \
                      '`convention`, `status`) values (%s, "%s", %s, "%s", "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['convention'],
                       i['status'])
                cursor.execute(sql)

            # Insert PSC List
            for i in self.list_psc:
                sql = 'insert into list_psc (`imo_number`, `name`, `mmsi`, `call_sign`, ' \
                      '`psc_org`, `authority`, `port_of_insp`, `type_of_insp`,' \
                      '`date_report`, `detention`, `duration`, `num_deficiencies`) values' \
                      '(%s, "%s", %s, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['psc_org'],
                       i['authority'], i['port_of_insp'], i['type_of_insp'], i['date_report'],
                       i['detention'], i['duration'], i['num_deficiencies'])
                cursor.execute(sql)
            # Insert deficiencies table
            for i in self.list_deficiencies:
                sql = 'insert into deficiencies (`imo_number`, `name`, `mmsi`, `call_sign`,' \
                      '`category`, `deficiency`, `number`) values' \
                      '(%s, "%s", %s, "%s", "%s", "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['category'],
                       i['deficiency'], i['number'])
                cursor.execute(sql)
            # Insert history name table
            for i in self.history_name:
                sql = 'insert into history_name (`imo_number`, `name`, `mmsi`, `call_sign`,' \
                      '    `former_name`, `date_effect`, `source`) values' \
                      '   (%s, "%s", %s, "%s", "%s", "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['former_name'],
                       i['date_effect'], i['source'])
                cursor.execute(sql)
            # Insert history flag table
            for i in self.history_flag:
                sql = 'insert into history_flag (`imo_number`, `name`, `mmsi`, `call_sign`,' \
                      '    `flag`, `date_effect`, `source`) values' \
                      '   (%s, "%s", %s, "%s", "%s", "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['flag'],
                       i['date_effect'], i['source'])
                cursor.execute(sql)
            conn.commit()
            # Insert history class
            for i in self.history_class:
                sql = 'insert into history_class (`imo_number`, `name`, `mmsi`, `call_sign`,' \
                      '`class_society`, `date_survey`, `source`) values' \
                      '(%s, "%s", %s, "%s", "%s", "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['class_society'],
                       i['date_survey'], i['source'])
                cursor.execute(sql)
            # Insert history company
            for i in self.history_company:
                sql = 'insert into history_company (`imo_number`, `name`, `mmsi`, `call_sign`,' \
                      '`company`, `role`, `date_effect`, `source`) values' \
                      '(%s, "%s", %s, "%s", "%s", "%s", "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['company'],
                      i['role'], i['date_effect'], i['source'])
                cursor.execute(sql)
            # Insert company overview
            for i in self.company_overview:
                sql = 'insert into company_overview (`imo_number`, `name`, `mmsi`, `call_sign`,' \
                      '        `imo_company`, `overview`, `value`) values' \
                      '       (%s, "%s", %s, "%s", %s, "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['imo_company'],
                       i['overview'], i['value'])
                cursor.execute(sql)
            # Insert document compliance record
            for i in self.doc_compliance:
                sql = 'insert into doc_compliance (`imo_number`, `name`, `mmsi`, `call_sign`,' \
                      '      `imo_company`, `flag`, `ship_type`,`class_society`,' \
                      '      `status`, `date_of_status`, `reason`) values' \
                      '     (%s, "%s", %s, "%s", %s, "%s", "%s", "%s", "%s",' \
                      '     "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['imo_company'],
                       i['flag'], i['ship_type'], i['class_society'], i['status'], i['date_of_status'],
                       i['reason'])
                cursor.execute(sql)
            # Insert synthesis inspection
            for i in self.synthesis_inspection:
                sql = 'insert into synthesis_inspection (`imo_number`, `name`, `mmsi`, `call_sign`,' \
                      '            `imo_company`, `role`, `nb_ships`,`last_3y_this_company_insp`,' \
                      '            `last_3y_this_company_dete`, `last_3y_all_company_insp`,' \
                      '            `last_3y_all_company_dete`) values' \
                      '           (%s, "%s", %s, "%s", %s, "%s", "%s", "%s", "%s",' \
                      '           "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['imo_company'],
                       i['role'], i['nb_ships'], i['last_3y_this_company_insp'], i['last_3y_this_company_dete'],
                       i['last_3y_all_company_insp'], i['last_3y_all_company_dete'])
                cursor.execute(sql)
            # Insert fleet
            for i in self.fleet:
                sql = 'insert into fleet (`imo_number`, `name`, `mmsi`, `call_sign`,' \
                      ' `imo_company`, `ship_imo_and_name`, `tonnage`,`ship_type`,' \
                      ' `year_build`, `current_flag`, `current_class`, `detentions_3yr_this_comp`,' \
                      ' `detentions_3yr_all_comp`, `acting_as`) values' \
                      '(%s, "%s", %s, "%s", %s, "%s", %s, "%s", "%s",' \
                      '"%s", "%s", "%s", "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['imo_company'],
                      i['imo_ship_name'], i['tonnage'], i['ship_type'], i['year_build'], i['current_flag'],
                      i['current_class'], i['detentions_3yr_this_comp'], i['detentions_3yr_all_comp'],
                      i['acting_as'])
                cursor.execute(sql)
            # Insert class key
            for i in self.class_key:
                sql = 'insert into class_key (`imo_number`, `name`, `mmsi`, `call_sign`,' \
                      '`imo_company`, `abbr`, `name_of_society`) values' \
                      '(%s, "%s", %s, "%s", %s, "%s", "%s");' % \
                      (self.imo_number, self.name, self.mmsi, self.call_sign, i['imo_company'],
                       i['abbr'], i['name_of_society'])
                cursor.execute(sql)
            conn.commit()
            try:
                # Insert company info
                for i in self.company_info:
                    sql = 'insert into company_info(`imo_company`, `name`, `address`, `last_update`) ' \
                          'values(%s, "%s", "%s", "%s");' % (i['imo_company'], i['name'], i['address'], \
                           i['last_update'])
                    log('Company IMO: ' + i['imo_company'])
                    cursor.execute(sql)
                conn.commit()
            except sqlite3.IntegrityError, e:
                log(e.message)

            log('#%s Ship successfully written into DB - %d.' % (self.imo_number, cursor.rowcount))
        except Exception, ex:
            log('DB EXCEPTION: %s' % ex.message)
            if re.search('locked', ex.message):
                self.Commit()
                time.sleep(random.uniform(0.5, 7))

