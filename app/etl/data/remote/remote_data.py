from enum import Enum
from pandas import DataFrame
from app.etl.data.base_data_types import IExtractor, FieldPathBase
from app.etl.data.remote.gee.google_earth_api_data_collector import (
    GoogleEarthAPIDataCollector,
)


class RemoteDataTypes(Enum):
    """Remote Types"""

    GEE = "gee"


class GEEDataExtractor(FieldPathBase, IExtractor):
    def __init__(self, path: str):
        FieldPathBase.__init__(self, path)
        self.path_parts = self.path.split("|")
        self.gee_api_collector = GoogleEarthAPIDataCollector(self.path_parts[0])

    def extract(self) -> DataFrame:
        import re

        # Check for AREA{...} syntax
        full_path = self.path
        area_match = re.search(r'AREA\(\((.+)\)\)', full_path)

        if area_match:
            # Extract everything before AREA{
            before_area = full_path[:area_match.start()].strip('|')
            parts = before_area.split('|')
            # parts[0] = project
            # parts[1] = dataset
            # parts[2] = start_date
            # parts[3] = end_date

            # Parse coordinates from AREA{(x1,y1),(x2,y2),...}
            coord_str = area_match.group(1)
            # Find all (lon, lat) pairs
            pairs = re.findall(r'([\d.+-]+)\s*,\s*([\d.+-]+)', coord_str)
            coords = [[float(lon), float(lat)] for lon, lat in pairs]

            return self.gee_api_collector.collect_area(
                dataset=parts[1],
                start_date=parts[2],
                end_date=parts[3],
                coordinates=coords,
            )
        else:
            # Check if we have enough parts before accessing them
            if len(self.path_parts) < 7:
                raise ValueError(
                    f"Invalid path format. Expected 7 parts separated by '|', "
                    f"but got {len(self.path_parts)}. Path: {self.path}"
                )

            return self.gee_api_collector.collect(
                start_date=self.path_parts[2],
                end_date=self.path_parts[3],
                longitude=float(self.path_parts[5]),
                latitude=float(self.path_parts[4]),
                scale=float(self.path_parts[6]),
            )
