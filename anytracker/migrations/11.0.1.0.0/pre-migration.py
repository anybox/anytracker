def migrate(cr, version):
    title = 'anytracker migration script {} to 11.0.1.0.0'.format(version)
    separator = '_' * 60

    print(separator)
    print()
    print(title)
    print(separator)

    def _execute(sql):
        print(sql)
        cr.execute(sql)
        print(cr.rowcount, 'row(s)')

    def unactivate_depreciated_views():
        view_external_ids = [
            'invoicing_ticket_view_form',
            'invoicing_bouquet_form',
            'invoicing_ticket_view_search',
            'priority_form_with_invoicing',
            'priority_tree_with_invoicing',
        ]

        sql_pattern_get_res_id = """
select res_id from ir_model_data
where module='anytracker'" and model='ir.ui.view' and name in ({xmlids})"""

        sql_pattern_unactive = "update ir_ui_view set active=False where id in ({ids})"

        print('desactivate depreciated invoicing views')

        # ir_model_data: get view ids from xmlids
        print('ir_model_data: get view ids from xmlids (res_ids)')
        sql = sql_pattern_get_res_id.format(
            xmlids=','.join(["'{}'".format(xmlid) for xmlid in view_external_ids])
        )
        _execute(sql)
        res_ids = [str(r[0]) for r in cr.fetchall()]
        print(res_ids)

        if res_ids:
            print('')
            print('desactivate views')
            sql = sql_pattern_unactive.format(ids=','.join(res_ids))
            _execute(sql)

    unactivate_depreciated_views()
