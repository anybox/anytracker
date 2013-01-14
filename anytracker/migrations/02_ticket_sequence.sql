/* convert the number to an integer and fix the ticket sequence */
CREATE OR REPLACE FUNCTION pc_chartoint(chartoconvert character varying)
  RETURNS integer AS
$BODY$
SELECT CASE WHEN trim($1) SIMILAR TO '[0-9]+' 
        THEN CAST(trim($1) AS integer) 
    ELSE NULL END;

$BODY$
  LANGUAGE 'sql' IMMUTABLE STRICT;

ALTER TABLE anytracker_ticket ALTER COLUMN number TYPE integer USING pc_chartoint(number);

select setval('ir_sequence_053', (select max(number)+1 from anytracker_ticket), false);
update ir_sequence set number_next=(select last_value from ir_sequence_053) where id=53;
