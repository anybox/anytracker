update anytracker_ticket as t set method_id=(select method_id from anytracker_ticket where id=t.project_id) where not parent_id is NULL;
select id, name from anytracker_ticket as t where method_id!=(select method_id from anytracker_ticket where id=t.parent_id);
