openerp.anytracker = function(instance) {
    // instance is the main openerp object created, which contains all modules
    // we load the web module
    module = instance.web;
    module.ViewManagerAction.include({
        set_title: function() {
            this._super();
            // Replace the stupid Tickets title with the path to the active_id
            if (this.action.res_model == 'anytracker.ticket'
                && this.active_view == 'kanban'
                && this.action.context.active_id)
            {
                var id = this.action.context.active_id;
                var self = this;
                var tickets = new module.Model("anytracker.ticket");
                tickets.call('get_breadcrumb', [[id]]).done(function(result) {
                    var items = result[id];
                    var breadcrumbs = [];
                    for (var i=0; i < items.length; i++) {
                        breadcrumbs.push(_.str.sprintf(items[i].name))
                    }
                    var title = breadcrumbs.join(' / ');
                    self.$el.find('.oe_breadcrumb_item:last').html(title);
                })
            }
        }
    })
}
