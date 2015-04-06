-- Write Ship info

insert into ships (`imo_number`, `name`, `mmsi`, `call_sign`, `tonnage`, `type`,
                   `build_year`, `flag`, `status`, `last_update_time`) VALUES
                   (%s, "%s", %s, "%s", %s, "%s",
                   %s, "%s", "%s", "%s");

insert into overview (`imo_number`, `name`, `mmsi`, `call_sign`, `overview`, `value`) VALUES
                     (%s, "%s", %s, "%s", "%s", %s);

insert into classification_survey (`imo_number`, `name`, `mmsi`, `call_sign`,
                                   `class_society`, `last_renew_date`, `next_renew_date`) VALUES
                                  (%s, "%s", %s, "%s",
                                  "%s", "%s", "%s")

insert into classification_status (`imo_number`, `name`, `mmsi`, `call_sign`,
                                  `class_society`, `date_change_status`, `status`, `reason`) values
                                  (%s, "%s", %s, "%s", "%s", "%s", "%s", "%s");

insert into management_detail (`imo_number`, `name_ship`, `mmsi`, `call_sign`, `imo_company`,
                               `role`, `name_company`, `address`, `date_effect`) values
                              (%s, "%s", %s, "%s", "%s", "%s", "%s", "%s", "%s");

insert into smc (`imo_number`, `name`, `mmsi`, `call_sign`, `class_society`,
                 `date_survey`, `date_expiry`, `date_change_status`,
                 `status`, `reason`, `cv`) values
                (%s, "%s", %s, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s");

insert into pi_info (`imo_number`, `name`, `mmsi`, `call_sign`, `name_insurer`, `date_inception`)
             values (%s, "%s", %s, "%s", "%s", "%s", "%s", "%s", "%s");

insert into geo_info (`imo_number`, `name`, `mmsi`, `call_sign`,
                      `date_record`, `area`, `source`) values
                     (%s, "%s", %s, "%s", "%s", "%s", "%s");

insert into imo_conventions (`imo_number`, `name`, `mmsi`, `call_sign`,
                             `convention`, `status`) values
                            (%s, "%s", %s, "%s", "%s", "%s");

insert into list_psc (`imo_number`, `name`, `mmsi`, `call_sign`,
                      `psc_org`, `authority`, `port_of_insp`, `type_of_insp`,
                      `date_report`, `detention`, `duration`, `num_deficiencies`) values
                     (%s, "%s", %s, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s");

insert into psc_info (`imo_number`, `name`, `mmsi`, `call_sign`,
                      `year_of_build`, `tonnage`, `deadweight`, `type_ship`,
                      `flag_ship`, `class_society`, `particular_of_company`, `name_authority`,
                      `place_insp`, `date_insp`, `ship_detained`, `num_deficiencies`) values
                     (%s, "%s", %s, "%s", "%s", %s, %s, "%s", "%s", "%s", "%s", "%s",
                      "%s", "%s", "%s", "%s");

insert into deficiencies (`imo_number`, `name`, `mmsi`, `call_sign`,
                          `category`, `deficiency`, `number`) values
                         (%s, "%s", %s, "%s", "%s", "%s", "%s");

insert into history_name (`imo_number`, `name`, `mmsi`, `call_sign`,
                          `former_name`, `date_effect`, `source`) values
                         (%s, "%s", %s, "%s", "%s", "%s", "%s");

insert into history_flag (`imo_number`, `name`, `mmsi`, `call_sign`,
                          `flag`, `date_effect`, `source`) values
                         (%s, "%s", %s, "%s", "%s", "%s", "%s");

insert into history_class (`imo_number`, `name`, `mmsi`, `call_sign`,
                           `class_society`, `date_survey`, `source`) values
                          (%s, "%s", %s, "%s", "%s", "%s", "%s");

insert into history_company (`imo_number`, `name`, `mmsi`, `call_sign`,
                             `company`, `role`, `date_effect`, `source`) values
                            (%s, "%s", %s, "%s", "%s", "%s", "%s", "%s");

insert into company_overview (`imo_number`, `name`, `mmsi`, `call_sign`,
                              `imo_company`, `overview`, `value`) values
                             (%s, "%s", %s, "%s", %s, "%s", "%s");

insert into doc_compliance (`imo_number`, `name`, `mmsi`, `call_sign`,
                            `imo_company`, `flag`, `ship_type`,`class_society`,
                            `status`, `date_of_status`, `reason`) values
                           (%s, "%s", %s, "%s", %s, "%s", "%s", "%s", "%s",
                           "%s", "%s");

insert into synthesis_inspection (`imo_number`, `name`, `mmsi`, `call_sign`,
                                  `imo_company`, `role`, `nb_ships`,`last_3y_this_company_insp`,
                                  `last_3y_this_company_dete`, `last_3y_all_company_insp`,
                                  `last_3y_all_company_dete`) values
                                 (%s, "%s", %s, "%s", %s, "%s", "%s", "%s", "%s",
                                 "%s", "%s");

insert into fleet (`imo_number`, `name`, `mmsi`, `call_sign`,
                   `imo_company`, `imo_and_shipname`, `tonnage`,`ship_type`,
                   `year_build`, `current_flag`, `current_class`, `detentions_3yr_this_comp`,
                   `detentions_3yr_all_comp`, `acting_as`) values
                  (%s, "%s", %s, "%s", %s, "%s", %s, "%s", "%s",
                  "%s", "%s", "%s", "%s", "%s");

insert into class_key (`imo_number`, `name`, `mmsi`, `call_sign`,
                       `imo_company`, `abbr`, `name_of_society`) values
                      (%s, "%s", %s, "%s", %s, "%s", "%s");