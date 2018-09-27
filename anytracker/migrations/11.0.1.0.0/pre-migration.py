def migrate(cr, version):
    title = 'anytracker to 11.0.1.0.0 migration script'
    separator = '_' * 60

    print(separator)
    print()
    print(title)
    print(separator)

    def execute(sql):
        print(sql)
        cr.execute(sql)
        print(cr.rowcount, 'row(s)')

    def unactivate_depreciated_views():
        print()
        print('desactivate depreciated invoicing views')

        # ir_model_data: get view ids from xmlids
        print('')
        print('ir_model_data: get view ids from xmlids (res_ids)')
        sql = "select res_id from ir_model_data where module='anytracker' and model='ir.ui.view' and name in ('invoicing_ticket_view_form', 'invoicing_bouquet_form', 'invoicing_ticket_view_search', 'priority_form_with_invoicing', 'priority_tree_with_invoicing')"
        execute(sql)
        res_ids = [str(r[0]) for r in cr.fetchall()]
        print(res_ids)

        if res_ids:
            print('')
            print('desactivate views')
            sql = "update ir_ui_view set active=False where id in ({})".format(','.join(res_ids))
            execute(sql)

    unactivate_depreciated_views()
