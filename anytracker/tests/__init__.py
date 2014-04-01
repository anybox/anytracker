from ..bouquet.tests import test_bouquets
from ..complexity.tests import test_complexity
from ..stage.tests import test_stage
from ..assignment.tests import test_assignment
from ..notify.tests import test_notify
from . import test_anytracker

fast_suite = [
    test_bouquets,
    test_complexity,
    test_stage,
    test_assignment,
    test_notify,
    test_anytracker,
]
