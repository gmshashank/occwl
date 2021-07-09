import numpy as np

from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec, gp_Pnt2d
from OCC.Core.BRep import BRep_Tool, BRep_Tool_Curve, BRep_Tool_Continuity
from OCC.Core.GeomLProp import GeomLProp_SLProps
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.BRepGProp import brepgprop_LinearProperties
from OCC.Core.GProp import GProp_GProps
from OCC.Core.GeomAbs import GeomAbs_Line, GeomAbs_Circle, GeomAbs_Ellipse, GeomAbs_Hyperbola, GeomAbs_Parabola, GeomAbs_BezierCurve, GeomAbs_BSplineCurve, GeomAbs_OffsetCurve, GeomAbs_OtherCurve
from OCC.Core.TopAbs import TopAbs_REVERSED
from OCC.Extend import TopologyUtils
from OCC.Core.TopoDS import TopoDS_Edge
from OCC.Core.GCPnts import GCPnts_AbscissaPoint
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.ShapeAnalysis import ShapeAnalysis_Edge

import occwl.geometry.geom_utils as geom_utils
from occwl.geometry.interval import Interval
from occwl.shape import Shape

class Edge(Shape):
    """
    A topological edge in a solid model
    Represents a 3D curve bounded by vertices
    """
    def __init__(self, topods_edge):
        assert isinstance(topods_edge, TopoDS_Edge)
        self._edge = topods_edge
    
    def topods_shape(self):
        """
        Get the underlying OCC edge as a shape

        Returns:
            OCC.Core.TopoDS.TopoDS_Edge: Edge
        """
        return self._edge

    def topods_edge(self):
        """
        Get the underlying OCC edge type

        Returns:
            OCC.Core.TopoDS.TopoDS_Edge: Edge
        """
        return self._edge

    def __hash__(self):
        """
        Hash for the edge

        Returns:
            int: Hash value
        """
        return self.topods_edge().__hash__()
    
    def __eq__(self, other):
        """
        Equality check for the edge.

        NOTE: This function only checks if the edge is the same.
        It doesn't check the edge orienation, so 

        edge1 == edge2

        does not necessarily mean 

        edge1.reversed() == edge2.reversed()
        """
        return self.topods_edge().__hash__() == other.topods_edge().__hash__()
    
    def point(self, u):
        """
        Evaluate the edge geometry at given parameter

        Args:
            u (float): Curve parameter
        
        Returns:
            np.ndarray: 3D Point
        """
        if self.has_curve():
            pt = self.curve().Value(u)
            return geom_utils.gp_to_numpy(pt)
        # If the edge has no curve then return a point
        # at the origin.
        # It would ne nice to return the location of the 
        # vertex
        return np.array([0,0,0])

    def tangent(self, u):
        """
        Compute the tangent of the edge geometry at given parameter

        Args:
            u (float): Curve parameter

        Returns:
            np.ndarray: 3D unit vector
        """
        if self.has_curve():
            pt = gp_Pnt()
            der = gp_Vec()
            self.curve().D1(u, pt, der)
            der.Normalize()
            tangent = geom_utils.gp_to_numpy(der)
            if self.reversed():
                tangent = -tangent
            return tangent
        # If the edge has no curve then return 
        # a zero vector
        return np.array([0,0,0])
    
    def first_derivative(self, u):
        """
        Compute the first derivative of the edge geometry at given parameter

        Args:
            u (float): Curve parameter

        Returns:
            np.ndarray: 3D vector
        """
        if self.has_curve():
            pt = gp_Pnt()
            der = gp_Vec()
            self.curve().D1(u, pt, der)
            return geom_utils.gp_to_numpy(der)
        # If the edge has no curve then return 
        # a zero vector
        return np.array([0,0,0])

    def length(self):
        """
        Compute the length of the edge curve

        Returns:
            float: Length of the edge curve
        """
        if not self.has_curve():
            return 0.0
        geometry_properties = GProp_GProps()
        brepgprop_LinearProperties(self.topods_edge(), geometry_properties)
        return geometry_properties.Mass()

    def curve(self):
        """
        Get the edge curve geometry

        Returns:
            OCC.Geom.Handle_Geom_Curve: Interface to all curve geometry
        """
        return BRep_Tool_Curve(self._edge)[0]

    def specific_curve(self):
        """
        Get the specific edge curve geometry

        Returns:
            OCC.Geom.Handle_Geom_*: Specific geometry type for the curve geometry
                                    or None if the curve type is GeomAbs_OtherCurve
        """
        brep_adaptor_curve = BRepAdaptor_Curve(self._edge)
        curv_type = brep_adaptor_curve.GetType()
        if curv_type == GeomAbs_Line:
            return brep_adaptor_curve.Line()
        if curv_type == GeomAbs_Circle:
            return brep_adaptor_curve.Circle()
        if curv_type == GeomAbs_Ellipse:
            return brep_adaptor_curve.Ellipse()
        if curv_type == GeomAbs_Hyperbola:
            return brep_adaptor_curve.Hyperbola()
        if curv_type == GeomAbs_Parabola:
            return brep_adaptor_curve.Parabola()
        if curv_type == GeomAbs_BezierCurve:
            return brep_adaptor_curve.BezierCurve()
        if curv_type == GeomAbs_BSplineCurve:
            return brep_adaptor_curve.BSpline()
        if curv_type == GeomAbs_OffsetCurve:
            return brep_adaptor_curve.OffsetCurve()
        return None

    def has_curve(self):
        """
        Does this edge have a valid curve?
        Some edges don't.  For example the edge at the pole of a sphere.

        Returns:
            bool: Whether this edge has a valid curve
        """
        curve = BRepAdaptor_Curve(self.topods_edge())
        return curve.Is3DCurve() 

    def u_bounds(self):
        """
        Parameter domain of the curve

        Returns:
            occwl.geometry.Interval: a 1D interval [u_min, u_max]
        """
        if not self.has_curve():
            # Return an empty interval
            return Interval()
        _, umin, umax = BRep_Tool_Curve(self.topods_edge())
        return Interval(umin, umax)
    
    def reversed_edge(self):
        """
        Return a copy of this edge with the orientation reversed.
        
        Returns:
            occwl.edge.Edge: An edge with the opposite orientation to this edge.
        """
        return Edge(self.topods_edge().Reversed())
    
    def closed_curve(self):
        """
        Returns whether the 3D curve of this edge is closed.
        i.e. the start and edge points are coincident.
        
        Returns:
            bool: If closed
        """
        return self.curve().IsClosed()

    def closed_edge(self):
        """
        Returns whether the edge forms a closed ring.  i.e.
        whether the start and end vertices are the same.
        
        Returns:
            bool: If closed
        """
        return BRep_Tool().IsClosed(self.topods_edge())

    def seam(self, face):
        """
        Whether this edge is a seam

        Args:
            face (occwl.face.Face): Face where the edge lives

        Returns:
            bool: If seam
        """
        return ShapeAnalysis_Edge().IsSeam(self.topods_edge(), face.topods_face())

    def periodic(self):
        """
        Whether this edge is periodic

        Returns:
            bool: If periodic
        """
        return BRepAdaptor_Curve(self.topods_edge()).IsPeriodic()

    def rational(self):
        """
        Whether this edge geometry is rational

        Returns:
            bool: If rational
        """
        return BRepAdaptor_Curve(self.topods_edge()).IsRational()

    def continuity(self, face1, face2):
        """
        Get the order of continuity among a pair of faces

        Args:
            face1 (occwl.face.Face): First face
            face2 (occwl.face.Face): Second face

        Returns:
            GeomAbs_Shape: enum describing the continuity order
        """
        return BRep_Tool_Continuity(self.topods_edge(), face1.topods_face(), face2.topods_face())

    def reversed(self):
        """
        Whether this edge is reversed with respect to the curve geometry

        Returns:
            bool: If rational
        """
        return self.topods_edge().Orientation() == TopAbs_REVERSED
    
    def curve_type(self):
        """
        Get the type of the curve geometry

        Returns:
            str: Type of the curve geometry
        """
        curv_type = BRepAdaptor_Curve(self._edge).GetType()
        if curv_type == GeomAbs_Line:
            return "line"
        if curv_type == GeomAbs_Circle:
            return "circle"
        if curv_type == GeomAbs_Ellipse:
            return "ellipse"
        if curv_type == GeomAbs_Hyperbola:
            return "hyperbola"
        if curv_type == GeomAbs_Parabola:
            return "parabola"
        if curv_type == GeomAbs_BezierCurve:
            return "bezier"
        if curv_type == GeomAbs_BSplineCurve:
            return "bspline"
        if curv_type == GeomAbs_OffsetCurve:
            return "offset"
        if curv_type == GeomAbs_OtherCurve:
            return "other"
        return "unknown"


    def tolerance(self):
        """
        Get tolerance of this edge.  The 3d curve of the edge should not
        deviate from the surfaces of adjacent faces by more than this value

        Returns:
            float The edge tolerance
        """
        return BRep_Tool().Tolerance(self._edge)


    def find_left_and_right_faces(self, faces):
        """
        Given a list of 1 or 2 faces which are adjacent to this edge,
        we want to return the left and right face when looking from 
        outside the solid.

                      Edge direction
                            ^
                            |   
                  Left      |   Right 
                  face      |   face
                            |

        In the case of a cylinder the left and right face will be
        the same.

        Args:
            faces (list(occwl.face.Face): The faces

        Returns:
            occwl.face.Face, occwl.face.Face: The left and then right face
        """
        assert len(faces) > 0
        face1 = faces[0]
        if len(faces) == 1:
            face2 = faces[0]
        else:
            face2 = faces[1]

        if face1.is_left_of(self):
            # In some cases (like a cylinder) the left and right faces
            # of the edge are the same face
            if face1 != face2:
                assert not face2.is_left_of(self)
            left_face = face1
            right_face = face2
        else:
            assert face2.is_left_of(self)
            left_face = face2
            right_face = face1

        return left_face, right_face