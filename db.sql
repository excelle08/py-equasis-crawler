create database equasis;
use equasis;


create table ships (
    `imo_number` INT(8) NOT NULL primary key,
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `tonnage` int(8),
    `DWT` varchar(6),
    `type` varchar(64),
    `build_year` varchar(11),
    `flag` varchar(20),
    `status` varchar(40),
    `last_update_time` varchar(11)
);create table overview (
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `overview` text,
    `value` varchar(10)
);create table classification_survey (
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `class_society` text,
    `last_renew_date` varchar(12),
    `next_renew_date` varchar(12)
);create table classification_status (
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `class_society` text,
    `date_change_status` varchar(32),
    `status` varchar(32),
    `reason` text
);create table management_detail (
    `imo_number_ship` INT(8),
    `name_ship` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `imo_company` varchar(8),
    `role` text,
    `name_company` text,
    `address` text,
    `date_effect` varchar(32)
);create table smc (
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `class_society` text,
    `date_survey` varchar(12),
    `date_expiry` varchar(12),
    `date_change_status` varchar(12),
    `status` varchar(32),
    `reason` text,
    `cv` text
);create table pi_info (
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `name_insurer` text,
    `date_inception` varchar(12)
);create table geo_info (
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `date_record` varchar(32),
    `area` text,
    `source` text
);create table imo_conventions (
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `convention` text,
    `status` text
);create table list_psc (
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `psc_org` varchar(32),
    `authority` text,
    `port_of_insp` text,
    `type_of_insp` text,
    `date_report` varchar(12),
    `detention` text,
    `duration` text,
    `num_deficiencies` text
);create table deficiencies(
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `category` text,
    `deficiency` text,
    `number` text
);create table history_name(
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `former_name` varchar(32),
    `date_effect` varchar(32),
    `source` varchar(32)
);create table history_flag(
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `flag` varchar(20),
    `date_effect` varchar(32),
    `source` varchar(32)
);create table history_class(
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `class_society` text,
    `date_survey` varchar(12),
    `source` text
);create table history_company(
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `company` text,
    `role` text,
    `date_effect` varchar(32),
    `source` varchar(32)
);create table company_overview(
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `imo_company` int(8),
    `overview` text,
    `value` text
);create table doc_compliance(
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `imo_company` int(8),
    `flag` text,
    `ship_type` text,
    `class_society` text,
    `status` text,
    `date_of_status` text,
    `reason` text
);create table synthesis_inspection(
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `imo_company` int(8),
    `role` text,
    `nb_ships` text,
    `last_3y_this_company_insp` text,
    `last_3y_this_company_dete` text,
    `last_3y_all_company_insp` text,
    `last_3y_all_company_dete` text
);create table fleet(
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `imo_company` int(8),
    `ship_imo_and_name` text,
    `tonnage` int(10),
    `ship_type` text,
    `year_build` varchar(4),
    `current_flag` text,
    `current_class` text,
    `detentions_3yr_this_comp` text,
    `detentions_3yr_all_comp` text,
    `acting_as` text
);create table class_key(
    `imo_number` INT(8),
    `name` varchar(32),
    `mmsi` int(10),
    `call_sign` varchar(8),
    `imo_company` int(8),
    `abbr` text,
    `name_of_society` text
);create table company_info(
    `imo_company` INT(8) primary key,
    `name` text,
    `address` text,
    `last_update` text
);
