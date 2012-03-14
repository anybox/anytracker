from osv import fields, osv

class ticket(osv.osv):
    _name = 'anytracker.ticket'
    _description = "Tickets for project management" 
    _columns = {
    'name' : fields.char('task name', 255, required=True),
    'infos' : fields.text('task description', required=False),
    'children' : fields.one2many('anytracker.ticket', 'parent','childre', required=False),
    'parent' : fields.many2one('anytracker.ticket','parent', required=False),
    'projectroot' : fields.boolean('is the root node', required=False),
    'level' : fields.selection([
                               (1,'Green'),(5,'Orange'),(10,'red')
                              ],'level')
                              ,
    'state' : fields.char('state', 30, required=False),
    'duration' :  fields.selection([
                    (0,'< half a day'),(None,'Will be computed'),
                (1,'Half a day')],'duration')
                    }
    
    _defaults = {
        'state' : 'Analyse',
        'duration' : 0,
        }

    def _autoroot(self, cr, uid, ids, context = None):
        """
        eases the process of checking constraints so as to guess the only possible root when applies
        """
        orphans = self._orphans(cr, uid, ids, context=context)
        roots = self._roots(cr, uid, ids, context=context)
        if len(oprhans) == 1:
            if not roots:
                orphans[0].set_root()
                return True
        else:
             return False    
       
    def _check_roots_orphans(self, cr, uid, ids, context = None):
        roots = self._roots(cr, uid, ids, context)
        orphans =  self._orphans(cr, uid, ids, context)
        if len(roots) == 1 and len(orphans) == 1:
            if roots[0].id == orphans[0].id:
                return True
        return False

    def _easy_check(self, cr, uid, context=None):
        return self._check_root_orphans(cr, uid, context=None
           ) or self._autoroot(cr, uid, context=None)
    

    def link_to_parent(self, cr, uid,**kw):
        pass

    def link_to_child(self, cr, uid,**kw):
        pass

    def split(self, cr, uid, **kw):
        pass

    def _roots(self, cr, uid, ids, context=None):
        nodes = self.browse(cr, uid, ids, context=context)
        result = []
        for node in nodes:
            if node.projectroot:
                result.append(node)
        return result

    def _orphans(self, cr, uid, ids, context=None):
        nodes =  self.browse(cr, uid, ids, context=context)
        orphans = []
        for node in nodes:
            if not node.parents:
                orphans.append(node)
        return orphans
        
    def _set_root(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'root': True},context=context)

    def _check_roots(self, cr, uid, ids, context=None):
        roots = _roots(self, cd, uid, ids, context=context)
        if len(roots) == 1:
            return True
        else:
            return False
    
#=========================================================================
#Devrait renvoyer Bool,roots afin de de pas appeler deux fois _roots
#une fois pour la verif et une fois pour savoir quels sont les noeuds
#en cause
#========================================================================
  
ticket()

