from ..bouquet.tests import test_bouquets
from ..complexity.tests import test_complexity
from ..stage.tests import test_stage
from ..assignment.tests import test_assignment
from ..notify.tests import test_notify
from . import test_anytracker
from ..invoicing.tests import test_invoicing
from ..mindmap.tests import test_import_export_mindmap
from ..method.tests import test_method

fast_suite = [
    test_bouquets,
    test_complexity,
    test_stage,
    test_assignment,
    test_notify,
    test_anytracker,
    test_invoicing,
    test_import_export_mindmap,
    test_method,
]
