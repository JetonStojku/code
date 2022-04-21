
-- we save the history of changed state in a table
create table punekerkues_status_history
(
    id                   serial not null
        constraint punekerkues_status_history_pkey
            primary key,
    name                 varchar,
    date                 timestamp,
    old_state            varchar,
    new_state            varchar,
    user_id              integer
        constraint punekerkues_status_history_user_id_fkey
            references res_users
            on delete set null,
    company_id           integer
        constraint punekerkues_status_history_company_id_fkey
            references res_company
            on delete set null,
    deactivate_reason_id integer
        constraint punekerkues_status_history_deactivate_reason_id_fkey
            references deactivate_reason_punekerkues
            on delete set null,
    punekerkues_id       integer
        constraint punekerkues_status_history_punekerkues_id_fkey
            references punekerkues_punekerkues
            on delete set null,
    create_uid           integer
        constraint punekerkues_status_history_create_uid_fkey
            references res_users
            on delete set null,
    create_date          timestamp,
    write_uid            integer
        constraint punekerkues_status_history_write_uid_fkey
            references res_users
            on delete set null,
    write_date           timestamp,
    migration_id         integer
);

-- table example value
-- id,name,date,old_state,new_state,user_id
-- 33,,2018-04-13 12:42:46.127000,,pasiv,1550
-- 35,,2018-04-13 13:54:07.170000,,pasiv,1570
-- 39,,2018-04-14 11:02:13.463000,,pasiv,1490
-- 40,,2018-04-16 08:56:15.283000,,pasiv,1195
-- 240991,Ndryshim statusi nga Regjistruar në Punëkërkues,2021-02-10 09:59:33.000000,draft,registered,1
-- 240992,Ndryshim statusi nga Punëkërkues në Nivel punësueshmërie,2021-02-10 10:02:11.000000,registered,categorized,1
-- 240993,Ndryshim statusi nga Nivel punësueshmërie në Punëkërkues i papunë,2021-02-10 10:16:40.000000,categorized,job_seeker,1




-- the view create a new form of this table to take the interval when the unempoyed is in this state. We want to count the number of first time you are in this state
CREATE or REPLACE VIEW __punekerkues_status_history as
(
select psh.*, rc.id zyra_vendore_id
from (
         select punekerkues_id,
                date::date,
                COALESCE(lead(date::date) over (partition by punekerkues_id order by punekerkues_id desc, date), (now() + interval '1' day)::date)                              next_date,
                COALESCE(FIRST_VALUE(date::date) over (partition by punekerkues_id, new_state order by punekerkues_id desc, new_state, date), (now() + interval '1' day)::date) first_date,
                new_state                                                                                                                                                       state
         from punekerkues_status_history
         group by punekerkues_id, date, old_state, new_state
     ) psh
         inner join punekerkues_punekerkues pp on pp.id = psh.punekerkues_id
         left join res_company rc on pp.company_id = rc.id);

-- result example of view
-- 148724,2021-08-31,2021-09-01,2021-08-31,draft,1
--  148724,2021-09-01,2022-04-22,2021-09-01,registered,1
--  148704,2021-08-19,2022-04-22,2021-08-19,draft,
--  148703,2021-08-19,2022-04-22,2021-08-19,draft,
--  148702,2021-08-19,2021-08-19,2021-08-19,draft,185
--  148702,2021-08-19,2022-04-22,2021-08-19,job_seeker,185
--  148702,2021-08-19,2021-08-19,2021-08-19,registered,185

-- the query below find how much users are in states: 'job_seeker', 'pasiv', 'pause'
-- and how mutch are for the first time in states: 'draft', 'job_seeker', 'registered'
-- I create a json format to take easy the data in python report
select Data_ne_dite, name,  '{' || string_agg('"' || total.state::varchar || '":' || total.c, ',') || '}'
       from (SELECT TO_CHAR(t.day, 'dd.mm.yyyy') Data_ne_dite, rc.name, '_' || psh.state state, count(psh) c
FROM generate_series(timestamp '2021-10-01', timestamp '2021-10-3', interval '1 day') AS t(day)
         inner join __punekerkues_status_history psh
                    on psh.state in ('job_seeker', 'pasiv', 'pause') and t.day::date between psh.date and psh.next_date
         left join res_company rc on psh.zyra_vendore_id = rc.id
group by 1, 2, 3
       having rc.name = 'ZV AKPA Berat'
union all
SELECT TO_CHAR(t.day, 'dd.mm.yyyy') Data_ne_dite, rc.name, '__' || psh.state state, count(psh) c
FROM generate_series(timestamp '2021-10-01', timestamp '2021-10-3', interval '1 day') AS t(day)
         inner join __punekerkues_status_history psh
                    on state in ('draft', 'job_seeker', 'registered') and t.day::date = psh.date and psh.date = psh.first_date
         left join res_company rc on psh.zyra_vendore_id = rc.id
group by 1, 2, 3
           having rc.name = 'ZV AKPA Berat') as total
group by 1, 2;

select Data_ne_dite, coalesce(drejtoria_rajonale, '') drejtoria_rajonale, coalesce(zyra_vendore, '') zyra_vendore,  '{' || string_agg('"' || total.state::varchar || '":' || total.c, ',') || '}' total_counts
       from (SELECT TO_CHAR(t.day, 'dd.mm.yyyy') Data_ne_dite, rcp.name drejtoria_rajonale, rc.name zyra_vendore, '_' || psh.state state, count(psh) c
FROM generate_series(timestamp '2021-10-01', timestamp '2021-10-3', interval '1 day') AS t(day)
         inner join __punekerkues_status_history psh
                    on psh.state in ('draft', 'job_seeker', 'registered') and t.day::date = psh.date and psh.date = psh.first_date
         left join res_company rc on psh.zyra_vendore_id = rc.id
       left join res_company rcp on rc.parent_id = rcp.id
group by 1, 2, 3, 4
       having rc.name in ('ZV AKPA Berat')
union all
    SELECT TO_CHAR(t.day, 'dd.mm.yyyy') Data_ne_dite, rcp.name drejtoria_rajonale, rc.name zyra_vendore, '__' || psh.state state, count(psh) c
FROM generate_series(timestamp '2021-10-01', timestamp '2021-10-3', interval '1 day') AS t(day)
         inner join __punekerkues_status_history psh
                    on psh.state in ('job_seeker', 'pasiv', 'pause') and t.day::date between psh.date and psh.next_date
         left join res_company rc on psh.zyra_vendore_id = rc.id
       left join res_company rcp on rc.parent_id = rcp.id
group by 1, 2, 3, 4
           having rc.name in ('ZV AKPA Berat')
) as total
group by 1, 2, 3
order by 1, 2, 3;

-- example result
-- date,department,office,total_counts (json format to take easy data in report)
-- 01.10.2021,DR AKPA Berat,ZV AKPA Berat,"{""__pasiv"":1,""__job_seeker"":1475}"
-- 02.10.2021,DR AKPA Berat,ZV AKPA Berat,"{""__pasiv"":1,""__job_seeker"":1475}"
-- 03.10.2021,DR AKPA Berat,ZV AKPA Berat,"{""__job_seeker"":1475,""__pasiv"":1}"
