"""
TODO: Add module description
"""

from aoe2mapgenerator.src.map.map import Map


class TemplateCreator:
    """
    Class to create a template from a map
    """

    def __init__(self):
        self.map = self.create_map()

    def create_map(self, map_size: int = 50) -> Map:
        """
        Create the map from the template
        """
        self.map = Map(map_size)
        return self.map

    # def fill_template(self, template: str) -> None:
    #     """
    #     Place the template on the map
    #     """
    #     self.map.place_template(
    #         'oak_forest.yaml',
    #         map_layer_type_list = [MapLayerType.UNIT, MapLayerType.TERRAIN, MapLayerType.ZONE, MapLayerType.DECOR],
    #         array_space_type_list = [zone, (TerrainId.GRASS_2, PlayerId.GAIA), zone, zone],
    #         player_id = PlayerId.ONE,
    #     )

    def overlay_template_map_onto_base_map(
        self, template_map: Map, base_map: Map, x_location: int, y_location: int
    ) -> None:
        """
        Overlay the template map onto the base map

        Args:
            template_map (Map): The map to overlay
            base_map (Map): The map to overlay onto
            x_location (int): The x location to overlay the map
            y_location (int): The y location to overlay the map
        """

        all_map_layers = template_map.get_all_map_layers()

        for map_layer in all_map_layers:

            map_layer_array = map_layer.get_array()

            for i, row in enumerate(map_layer_array):
                for j, cell in enumerate(row):
                    base_map.set_point(i + x_location, j + y_location, cell[0], cell[1])
