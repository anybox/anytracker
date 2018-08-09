/**
odoo.anytracker = function(instance, local) {
    // instance is the main openerp object created, which contains all modules
    // we load the web module
    instance.web.ViewManagerAction.include({
        set_title: function() {
            this._super();
            // Replace the stupid Tickets title with the path to the active_id
            if (this.action.res_model == 'anytracker.ticket'
                && this.active_view == 'kanban'
                && this.action.context.active_id)
            {
                var id = this.action.context.active_id;
                var self = this;
                var tickets = new instance.web.Model("anytracker.ticket");
                tickets.call('get_breadcrumb', [[id]]).done(function(result) {
                    var breadcrumbs = [];
                    for (var i=0; i < result.length; i++) {
                        breadcrumbs.push(_.str.sprintf(result[i].name))
                    }
                    var title = breadcrumbs.join(' / ');
                    self.$el.find('.oe_breadcrumb_item:last').html(title);
                })
            }
        }
    });
    instance.web_kanban.KanbanRecord.include({
        kanban_gravatar: function(email, size) {
            size = size || 22;
            email = _.str.trim(email || '').toLowerCase();
            var default_ = _.str.isBlank(email) ? 'mm' : 'identicon';
            var email_md5 = $.md5(email);
            return '//www.gravatar.com/avatar/' + email_md5 + '.png?s=' + size + '&d=' + default_;
        }
    });
}
**/

odoo.define('anytracker.update_kanban', function (require) {
"use strict";

var Model = required('web.Model');
var ViewManagerAction = require('web.ViewManagerAction');
var KanbanRecord = require('web.KanbanRecord');

ViewManagerAction.include({
    set_title: function() {
        this._super();
        // Replace the stupid Tickets title with the path to the active_id
         
        if (this.action.res_model == 'anytracker.ticket'
            && this.active_view == 'kanban'
            && this.action.context.active_id)
        {
            var id = this.action.context.active_id;
            var self = this;
            var tickets = new Model("anytracker.ticket");
            tickets.call('get_breadcrumb', [[id]]).done(function(result) {
                var breadcrumbs = [];
                for (var i=0; i < result.length; i++) {
                    breadcrumbs.push(_.str.sprintf(result[i].name))
                }
                var title = breadcrumbs.join(' / ');                    
                self.$el.find('.oe_breadcrumb_item:last').html(title);
            })
        }
    }
});

KanbanRecord.include({
    kanban_gravatar: function(email, size) {
        size = size || 22;
        email = _.str.trim(email || '').toLowerCase();
        var default_ = _.str.isBlank(email) ? 'mm' : 'identicon';
        var email_md5 = $.md5(email);
        return '//www.gravatar.com/avatar/' + email_md5 + '.png?s=' + size + '&d=' + default_;
    }
});

});
