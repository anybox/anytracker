/* add a number to each old ticket */
update anytracker_ticket set number=id;
update ir_sequence set number_next=1+(select max(id) from anytracker_ticket) where code='anytracker.ticket';
