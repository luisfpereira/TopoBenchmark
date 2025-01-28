"""Graph2GraphLifting module with automated exports."""

from topobenchmark.transforms._utils import discover_objs
from topobenchmark.transforms.liftings.base import LiftingMap

GRAPH2GRAPH_LIFTINGS = discover_objs(
    __file__,
    condition=lambda name, obj: issubclass(obj, LiftingMap),
)

locals().update(GRAPH2GRAPH_LIFTINGS)
