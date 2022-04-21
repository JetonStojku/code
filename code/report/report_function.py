    def generate_xlsx_report(self, workbook, data, assets):

        # Header i excel
        zyrat = data.get('zyre_ids')
        drejtorite = data.get('drejtori_ids')
        date_fillimi = data.get('date_fillimi')
        date_mbarimi = data.get('date_mbarimi')

        if zyrat:
            sql = """
                    select Data_ne_dite, coalesce(drejtoria_rajonale, '') drejtoria_rajonale, coalesce(zyra_vendore, '') zyra_vendore,  '{' || string_agg('"' || total.state::varchar || '":' || total.c, ',') || '}' total_counts
                           from (SELECT TO_CHAR(t.day, 'dd.mm.yyyy') Data_ne_dite, rcp.name drejtoria_rajonale, rc.name zyra_vendore, '_' || psh.state state, count(psh) c
                    FROM generate_series(timestamp %s, timestamp %s, interval '1 day') AS t(day)
                             inner join __punekerkues_status_history psh
                                        on psh.state in ('draft', 'job_seeker', 'registered') and t.day::date = psh.date and psh.date = psh.first_date
                             left join res_company rc on psh.zyra_vendore_id = rc.id
                           left join res_company rcp on rc.parent_id = rcp.id
                    group by 1, 2, 3, 4
                           having rc.name in %s
                    union all
                        SELECT TO_CHAR(t.day, 'dd.mm.yyyy') Data_ne_dite, rcp.name drejtoria_rajonale, rc.name zyra_vendore, '__' || psh.state state, count(psh) c
                    FROM generate_series(timestamp %s, timestamp %s, interval '1 day') AS t(day)
                             inner join __punekerkues_status_history psh
                                        on psh.state in ('job_seeker', 'pasiv', 'pause') and t.day::date between psh.date and psh.next_date
                             left join res_company rc on psh.zyra_vendore_id = rc.id
                           left join res_company rcp on rc.parent_id = rcp.id
                    group by 1, 2, 3, 4
                               having rc.name in %s
                    ) as total
                    group by 1, 2, 3
                    order by 1, 2, 3
            """
            params = (data['date_fillimi'], data['date_mbarimi'], tuple(zyrat), data['date_fillimi'], data['date_mbarimi'], tuple(zyrat))
        elif drejtorite:
            sql = """
                    select Data_ne_dite, coalesce(drejtoria_rajonale, '') drejtoria_rajonale, coalesce(zyra_vendore, '') zyra_vendore,  '{' || string_agg('"' || total.state::varchar || '":' || total.c, ',') || '}' total_counts
                           from (SELECT TO_CHAR(t.day, 'dd.mm.yyyy') Data_ne_dite, rcp.name drejtoria_rajonale, rc.name zyra_vendore, '_' || psh.state state, count(psh) c
                    FROM generate_series(timestamp %s, timestamp %s, interval '1 day') AS t(day)
                             inner join __punekerkues_status_history psh
                                        on psh.state in ('draft', 'job_seeker', 'registered') and t.day::date = psh.date and psh.date = psh.first_date
                             left join res_company rc on psh.zyra_vendore_id = rc.id
                           left join res_company rcp on rc.parent_id = rcp.id
                    group by 1, 2, 3, 4
                           having rcp.name in %s
                    union all
                        SELECT TO_CHAR(t.day, 'dd.mm.yyyy') Data_ne_dite, rcp.name drejtoria_rajonale, rc.name zyra_vendore, '__' || psh.state state, count(psh) c
                    FROM generate_series(timestamp %s, timestamp %s, interval '1 day') AS t(day)
                             inner join __punekerkues_status_history psh
                                        on psh.state in ('job_seeker', 'pasiv', 'pause') and t.day::date between psh.date and psh.next_date
                             left join res_company rc on psh.zyra_vendore_id = rc.id
                           left join res_company rcp on rc.parent_id = rcp.id
                    group by 1, 2, 3, 4
                               having rcp.name in %s
                    ) as total
                    group by 1, 2, 3
                    order by 1, 2, 3
                    """
            params = (data['date_fillimi'], data['date_mbarimi'], tuple(drejtorite), data['date_fillimi'], data['date_mbarimi'], tuple(drejtorite))
        else:
            sql = """
                    select Data_ne_dite, coalesce(drejtoria_rajonale, '') drejtoria_rajonale, coalesce(zyra_vendore, '') zyra_vendore,  '{' || string_agg('"' || total.state::varchar || '":' || total.c, ',') || '}' total_counts
                           from (SELECT TO_CHAR(t.day, 'dd.mm.yyyy') Data_ne_dite, rcp.name drejtoria_rajonale, rc.name zyra_vendore, '_' || psh.state state, count(psh) c
                    FROM generate_series(timestamp %s, timestamp %s, interval '1 day') AS t(day)
                             inner join __punekerkues_status_history psh
                                        on psh.state in ('draft', 'job_seeker', 'registered') and t.day::date = psh.date and psh.date = psh.first_date
                             left join res_company rc on psh.zyra_vendore_id = rc.id
                           left join res_company rcp on rc.parent_id = rcp.id
                    group by 1, 2, 3, 4
                    union all
                        SELECT TO_CHAR(t.day, 'dd.mm.yyyy') Data_ne_dite, rcp.name drejtoria_rajonale, rc.name zyra_vendore, '__' || psh.state state, count(psh) c
                    FROM generate_series(timestamp %s, timestamp %s, interval '1 day') AS t(day)
                             inner join __punekerkues_status_history psh
                                        on psh.state in ('job_seeker', 'pasiv', 'pause') and t.day::date between psh.date and psh.next_date
                             left join res_company rc on psh.zyra_vendore_id = rc.id
                           left join res_company rcp on rc.parent_id = rcp.id
                    group by 1, 2, 3, 4
                    ) as total
                    group by 1, 2, 3
                    order by 1, 2, 3
            """
            params = (data['date_fillimi'], data['date_mbarimi'], data['date_fillimi'], data['date_mbarimi'])
        self.env.cr.execute(sql, params)
        results = self.env.cr.fetchall()

        worksheet = workbook.add_worksheet('PuPa regjistrime te reja, ne dite')

        def cell_format(cell_format_key, new_key=None):
            """@param cell_format_key: str key: header, document, totals, number,
            @param new_key: dict {}
            @return: cell format
            """
            dict_format = {
                'header': {'bold': True, 'border': True, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True, 'font_name': 'Calibri', 'font_size': 11},
                'document': {'border': True, 'valign': 'vcenter', 'align': 'left', 'text_wrap': False, 'font_name': 'Calibri', 'font_size': 11, 'color': 'black'},
                'totals': {'bold': True, 'border': True, 'align': 'right', 'valign': 'vcenter', 'font_name': 'Calibri', 'font_size': 11, 'text_wrap': False},
                'number': {'border': True, 'align': 'right', 'valign': 'vcenter', 'font_name': 'Calibri', 'font_size': 11, 'text_wrap': False},
            }
            if new_key:
                dict_format[cell_format_key].update(new_key)
            return workbook.add_format(dict_format[cell_format_key])

        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:C', 30)
        worksheet.set_column('D:F', 20)
        # Report Header
        worksheet.merge_range(0, 0, 0, 8, 'Periudha: {} - {}'.format(date_fillimi, date_mbarimi), cell_format('header'))
        worksheet.merge_range(1, 0, 1, 8, 'PuPa regjistrime te reja, ne dite', cell_format('header'))
        # Table header
        row = 3
        worksheet.write(row, 0, 'Data ne dite', cell_format('header'))
        worksheet.write(row, 1, 'Drejtoria Rajonale', cell_format('header'))
        worksheet.write(row, 2, 'Zyra Vendore', cell_format('header'))
        worksheet.write(row, 3, 'Regjistruar per here te pare ne AKPA', cell_format('header'))
        worksheet.write(row, 4, 'Nr PuPa te rinj', cell_format('header'))
        worksheet.write(row, 5, 'Nr Punekerkues te rinj', cell_format('header'))
        worksheet.write(row, 6, 'Nr PuPa', cell_format('header'))
        worksheet.write(row, 7, 'Nr Pasiv', cell_format('header'))
        worksheet.write(row, 8, 'Nr Pezull', cell_format('header'))
        for r in results:
            row += 1
            worksheet.write(row, 0, r[0], cell_format('document'))
            worksheet.write(row, 1, r[1], cell_format('document'))
            worksheet.write(row, 2, r[2], cell_format('document'))
            worksheet.write(row, 3, json.loads(r[3]).get('_draft', 0), cell_format('number'))
            worksheet.write(row, 4, json.loads(r[3]).get('_joob_seeker', 0), cell_format('number'))
            worksheet.write(row, 5, json.loads(r[3]).get('_registered', 0), cell_format('number'))
            worksheet.write(row, 6, json.loads(r[3]).get('__job_seeker', 0), cell_format('number'))
            worksheet.write(row, 7, json.loads(r[3]).get('__pasiv', 0), cell_format('number'))
            worksheet.write(row, 8, json.loads(r[3]).get('__pause', 0), cell_format('number'))
