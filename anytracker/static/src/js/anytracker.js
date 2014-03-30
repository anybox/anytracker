openerp.anytracker = function(instance) {
    // instance is the main openerp object created, which contains all modules
    // we load the web module
    module = instance.web
    module.ViewManagerAction.include({
        set_title: function() {
            // Replace the OpenERP breadcrumb with the Anytracker breadcrumb
            if (this.action.res_model != 'anytracker.ticket' || !this.action.view_mode || this.action.view_mode.slice(0, 6) != 'kanban') {
                return this._super();
            } else {
                this.breadcrumbs = [];
                id = this.action.context.active_id;
                var self = this;
                var tickets = new module.Model("anytracker.ticket");
                tickets.call('get_breadcrumb', [[id]]).done(function(result) {
                    var items = result[id]
                    var breadcrumbs = [];
                    for (var i=0; i < items.length; i++) {
                        breadcrumbs.push(_.str.sprintf('<span class="oe_breadcrumb_item">%s</span>', items[i].name))
                    }
                    var html_breadcrumb = breadcrumbs.join(' <span class="oe_fade">/</span> ');
                    self.$el.find('.oe_breadcrumb_title:first').html(html_breadcrumb);
                })
            }
        }
    })
}
